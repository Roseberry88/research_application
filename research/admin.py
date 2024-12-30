from django.contrib import admin
from .models import (
    Department,
    Research,
    ResearchBudget,
    ResearchApplication,
    PaymentMethod,
    Attachment
)

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import StaffRequest  # 상단 import 부분에 추가

from django.utils import timezone
from django.contrib import messages

from django.contrib import messages
from django.http import HttpResponseRedirect

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

class ResearchBudgetInline(admin.TabularInline):
    model = ResearchBudget
    extra = 1

@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = [
        'project_number',
        'project_name',
        'researcher',
        'contract_from',
        'contract_to',
        'total_budget'
    ]
    search_fields = ['project_number', 'project_name', 'researcher__username']
    list_filter = ['researcher']
    inlines = [ResearchBudgetInline]

class PaymentMethodInline(admin.StackedInline):
    model = PaymentMethod
    can_delete = False
    
class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1

@admin.register(ResearchBudget)
class ResearchBudgetAdmin(admin.ModelAdmin):
    list_display = [
        'get_project_number',
        'get_project_name',
        'get_researcher',
        'budget_type',
        'total_amount',
        'remaining_amount'
    ]
    list_filter = ['budget_type', 'research__researcher']
    search_fields = [
        'research__project_number', 
        'research__project_name', 
        'research__researcher__username'
    ]
    
    def get_project_number(self, obj):
        return obj.research.project_number
    get_project_number.short_description = '과제번호'
    
    def get_project_name(self, obj):
        return obj.research.project_name
    get_project_name.short_description = '과제명'
    
    def get_researcher(self, obj):
        return obj.research.researcher
    get_researcher.short_description = '연구책임자'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(research__researcher=request.user)

@admin.register(ResearchApplication)
class ResearchApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_number',
        'get_project_number',
        'get_project_name',
        'applicant',
        'application_date',
        'amount',
        'status'
    ]
    list_filter = ['status', 'application_date']
    search_fields = [
        'application_number',
        'research_budget__research__project_number',
        'research_budget__research__project_name'
    ]
    inlines = [PaymentMethodInline, AttachmentInline]
    
    def get_project_number(self, obj):
        return obj.research_budget.research.project_number
    get_project_number.short_description = '과제번호'
    
    def get_project_name(self, obj):
        return obj.research_budget.research.project_name
    get_project_name.short_description = '과제명'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(applicant=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # 새로운 객체 생성 시
            obj.applicant = request.user
        super().save_model(request, obj, form, change)

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'get_application_number', 'uploaded_at']
    search_fields = ['file_name', 'application__application_number']
    
    def get_application_number(self, obj):
        return obj.application.application_number
    get_application_number.short_description = '신청번호'

class CustomAdminSite(admin.AdminSite):
    def has_permission(self, request):
        # superuser인 경우에만 접근 가능하도록
        return request.user.is_active and request.user.is_superuser

@admin.register(StaffRequest)
class StaffRequestAdmin(admin.ModelAdmin):
    change_form_template = 'research/admin/staffrequest/change_form.html'
    
    # 목록 화면 설정
    list_display = ['desired_username', 'created_at', 'status']
    list_filter = ['status']
    search_fields = ['desired_username']
    
    # 상세 화면 설정
    fields = ['desired_username', 'reason', 'created_at']
    readonly_fields = ['created_at']

    def get_readonly_fields(self, request, obj=None):
        # 무조건 모든 필드를 읽기 전용으로 설정
        return ['desired_username', 'reason', 'created_at']

    def response_change(self, request, obj):
        if "_approve" in request.POST and obj.status == 'pending':
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # 새로운 staff 계정 생성
                user = User.objects.create_user(
                    username=obj.desired_username,
                    password=obj.password,
                    is_staff=True,
                    military_id=obj.desired_username
                )
                
                # 상태를 승인으로 변경
                obj.status = 'approved'
                obj.reviewed_at = timezone.now()
                obj.reviewed_by = request.user
                obj.save()
                
                self.message_user(request, f'"{obj.desired_username}" 계정이 승인되었습니다.')
                return HttpResponseRedirect('../../')
                
            except Exception as e:
                self.message_user(request, f'승인 중 오류 발생: {str(e)}', level=messages.ERROR)
    
        if "_reject" in request.POST and obj.status == 'pending':
            # 상태를 거절로 변경
            obj.status = 'rejected'
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
            obj.save()
            
            self.message_user(request, f'"{obj.desired_username}" 신청이 거절되었습니다.')
            return HttpResponseRedirect('../../')
            
        return super().response_change(request, obj)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update({
            'show_save': False,
            'show_save_and_continue': False,
            'show_save_and_add_another': False,
            'show_delete': False
        })
        # 대기중일 때만 승인/거절 버튼 표시
        context['show_approval_buttons'] = obj is None or obj.status == 'pending'
        return super().render_change_form(request, context, add, change, form_url, obj)

    def has_delete_permission(self, request, obj=None):
        return False  # 삭제 권한 제거
    
# Admin 사이트 재설정
admin_site = CustomAdminSite(name='custom_admin')

# 모델들을 새로운 admin_site에 등록
admin_site.register(Department, DepartmentAdmin)
admin_site.register(Research, ResearchAdmin)
admin_site.register(ResearchBudget, ResearchBudgetAdmin)
admin_site.register(ResearchApplication, ResearchApplicationAdmin)
admin_site.register(Attachment, AttachmentAdmin)
admin_site.register(StaffRequest, StaffRequestAdmin)