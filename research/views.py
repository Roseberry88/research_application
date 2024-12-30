from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from .models import (
    ResearchApplication, 
    ResearchBudget, 
    PaymentMethod, 
    Attachment,
    Department
)
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CustomAuthenticationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import SignUpForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Research, ResearchBudget, ResearchApplication
import xlsxwriter
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.decorators import user_passes_test  # admin_required 데코레이터를 위해

from django.db.models import Sum
from django.utils import timezone

from .forms import ResearchApplicationForm

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import UserBankAccount, ResearchCard, Research
import json

from django.views.decorators.http import require_POST
from django.contrib import messages

from django.core.exceptions import PermissionDenied
from functools import wraps

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.utils import timezone
from .models import StaffRequest
from .forms import StaffRequestForm
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from .forms import (
    ResearchForm,
    ResearchBudgetFormSet,
    ResearchBudgetForm,
)

from django.db.models import Q
from django.http import JsonResponse
from .models import User

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('research:login')
        if request.user.is_superuser:
            # superuser는 접근 불가 - admin 페이지 사용해야 함
            raise PermissionDenied
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def dashboard(request):
    # 검색 조건 처리
    applications = ResearchApplication.objects.select_related(
        'research_budget',
        'research_budget__research',
        'research_budget__research__researcher',
        'research_budget__research__researcher__department',
        'applicant'
    ).all()

    # 일반 사용자는 본인이 신청한 것만 볼 수 있도록 수정
    if not request.user.is_staff:
        applications = applications.filter(applicant=request.user)
    
    # 검색 필터 적용
    if request.GET:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        project_number = request.GET.get('project_number')
        project_name = request.GET.get('project_name')
        researcher = request.GET.get('researcher')
        budget_type = request.GET.get('budget_type')
        status = request.GET.get('status')

        if start_date and end_date:
            applications = applications.filter(application_date__range=[start_date, end_date])
        if project_number:
            applications = applications.filter(research_budget__research__project_number__icontains=project_number)
        if project_name:
            applications = applications.filter(research_budget__research__project_name__icontains=project_name)
        if researcher:
            applications = applications.filter(research_budget__research__researcher__username__icontains=researcher)
        if budget_type:
            applications = applications.filter(research_budget__budget_type=budget_type)
        if status:
            applications = applications.filter(status=status)

    context = {
        'applications': applications,
        'budget_types': ResearchBudget.TYPE_CHOICES,
        'status_choices': ResearchApplication.STATUS_CHOICES,
    }
    return render(request, 'research/dashboard.html', context)

@staff_required
def staff_dashboard(request):
    # 전체 연구과제 및 진행중인 연구과제 수 계산
    today = timezone.now().date()
    total_research = Research.objects.count()
    active_research = Research.objects.filter(
        contract_from__lte=today,
        contract_to__gte=today
    ).count()

    # 연구비 신청 통계
    applications = ResearchApplication.objects.select_related(
        'research_budget',
        'research_budget__research',
        'research_budget__research__researcher',
        'applicant'
    ).all()

    total_applications = applications.count()
    pending_applications = applications.filter(status='신청').count()

    # 예산 현황
    total_budget = Research.objects.aggregate(Sum('total_budget'))['total_budget__sum'] or 0
    used_budget = ResearchApplication.objects.filter(status='결재').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    # 최근 연구비 신청 목록 (최근 5개)
    recent_applications = applications.order_by('-id')[:5]

    context = {
        'total_research': total_research,
        'active_research': active_research,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'total_budget': total_budget,
        'used_budget': used_budget,
        'recent_applications': recent_applications,  # dashboard.html에서 사용하는 변수명으로 변경
        'applications': applications,  # 전체 목록도 함께 전달
        'budget_types': ResearchBudget.TYPE_CHOICES,
        'status_choices': ResearchApplication.STATUS_CHOICES,
    }
    return render(request, 'research/staff/dashboard.html', context)

@staff_required
def staff_research_list(request):
    researches = Research.objects.select_related(
        'researcher',
        'researcher__department'
    ).all()
    
    # 검색 필터 적용
    project_number = request.GET.get('project_number')
    project_name = request.GET.get('project_name')
    researcher = request.GET.get('researcher')
    
    if project_number:
        researches = researches.filter(project_number__icontains=project_number)
    if project_name:
        researches = researches.filter(project_name__icontains=project_name)
    if researcher:
        researches = researches.filter(
            Q(researcher__username__icontains=researcher) |
            Q(researcher__first_name__icontains=researcher)
        )
    
    context = {
        'researches': researches,
        'budget_types': ResearchBudget.TYPE_CHOICES,
    }
    return render(request, 'research/staff/research_list.html', context)

@staff_required
def staff_application_list(request):
    applications = ResearchApplication.objects.select_related(
        'research_budget',
        'research_budget__research',
        'research_budget__research__researcher',
        'applicant'
    ).all()

    # 검색 필터 적용
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_number = request.GET.get('project_number')
    applicant = request.GET.get('applicant')
    budget_type = request.GET.get('budget_type')
    status = request.GET.get('status')

    if start_date and end_date:
        applications = applications.filter(application_date__range=[start_date, end_date])
    if project_number:
        applications = applications.filter(research_budget__research__project_number__icontains=project_number)
    if applicant:
        applications = applications.filter(
            Q(applicant__username__icontains=applicant) |
            Q(applicant__first_name__icontains=applicant)
        )
    if budget_type:
        applications = applications.filter(research_budget__budget_type=budget_type)
    if status:
        applications = applications.filter(status=status)

    context = {
        'applications': applications,
        'budget_types': ResearchBudget.TYPE_CHOICES,
        'status_choices': ResearchApplication.STATUS_CHOICES,
    }
    return render(request, 'research/staff/application_list.html', context)

# 연구비 신청 목록 뷰
@login_required
def application_list(request):
    """연구비 신청 목록을 보여주고 검색 기능을 제공"""
    applications = ResearchApplication.objects.select_related(
        'research_budget',
        'research_budget__research',  # Research 모델 데이터
        'research_budget__research__researcher',  # 연구책임자 정보
        'research_budget__research__researcher__department',  # 소속 정보
        'applicant'
    ).all()
    
    # 검색 필터 적용
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_number = request.GET.get('project_number')
    status = request.GET.get('status')

    if start_date and end_date:
        applications = applications.filter(
            application_date__range=[start_date, end_date]
        )
    
    if project_number:
        applications = applications.filter(
            research_budget__research__project_number__icontains=project_number
        )
        
    if status:
        applications = applications.filter(status=status)

    # Staff가 아닌 경우에만 본인의 신청 내역으로 필터링
    if not request.user.is_staff:
        applications = applications.filter(applicant=request.user)

    context = {
        'applications': applications,
        'status_choices': ResearchApplication.STATUS_CHOICES,
    }
    return render(request, 'research/application_list.html', context)

# 연구비 신청서 상세 보기
@login_required
def application_detail(request, pk):
    """연구비 신청서의 상세 내용을 보여줌"""
    application = get_object_or_404(ResearchApplication, pk=pk)
    attachments = Attachment.objects.filter(application=application)
    payment_method = PaymentMethod.objects.filter(application=application).first()
    
    # 연구비 총액 계산
    total_budget = application.research_budget.get_total_research_budget()
    
    # 선택된 예산항목의 예산 금액
    budget_amount = application.research_budget.get_budget_amount()
    
    # 잔액 계산
    remaining_amount = application.research_budget.calculate_remaining_amount()
    
    context = {
        'application': application,
        'attachments': attachments,
        'payment_method': payment_method,
        'status_choices': ResearchApplication.STATUS_CHOICES,
        'total_budget': total_budget,
        'budget_amount': budget_amount,
        'remaining_amount': remaining_amount,
    }

    # staff 사용자인 경우 staff용 템플릿 사용
    if request.user.is_staff:
        return render(request, 'research/staff/application_detail.html', context)
    
    # 일반 사용자인 경우 기본 템플릿 사용
    return render(request, 'research/application_detail.html', context)

# @login_required
# def application_create(request):
#     if request.method == 'POST':
#         # 새 계좌 등록 처리
#         if 'bank_name' in request.POST and 'account_number' in request.POST and 'account_holder' in request.POST:
#             try:
#                 account = UserBankAccount.objects.create(
#                     user=request.user,
#                     bank_name=request.POST['bank_name'],
#                     account_number=request.POST['account_number'],
#                     account_holder=request.POST['account_holder']
#                 )
#                 messages.success(request, '새 계좌가 등록되었습니다.')
#                 return JsonResponse({
#                     'success': True,
#                     'id': account.id,
#                     'bank_name': account.bank_name,
#                     'account_number': account.account_number,
#                     'account_holder': account.account_holder
#                 })
#             except Exception as e:
#                 return JsonResponse({
#                     'success': False,
#                     'message': str(e)
#                 }, status=400)

#         # 연구비 신청 처리
#         form = ResearchApplicationForm(request.POST)
#         research_budget = get_object_or_404(ResearchBudget, pk=request.POST.get('research_budget'))
        
#         if form.is_valid():
#             application = form.save(commit=False)
#             application.research_budget = research_budget
#             application.applicant = request.user
#             application.status = '신청'
#             application.budget_subcategory = request.POST.get('budget_subcategory')
#             application.save()

#             # 지불 방법 처리
#             payment_type = request.POST.get('payment_type')
#             payment_method = PaymentMethod(
#                 application=application,
#                 is_card=(payment_type == 'card')
#             )
            
#             if payment_type == 'card':
#                 payment_method.card_id = request.POST.get('card')
#             else:
#                 payment_method.bank_account_id = request.POST.get('bank_account')
            
#             payment_method.save()
            
#             # 첨부 파일 처리
#             if request.FILES:
#                 for file in request.FILES.getlist('attachments'):
#                     Attachment.objects.create(
#                         application=application,
#                         file_name=file.name,
#                         file=file
#                     )
            
#             messages.success(request, '연구비 신청이 완료되었습니다.')
#             return redirect('research:application_detail', pk=application.pk)
    
#     # GET 요청 처리
#     researches = Research.objects.filter(
#         Q(researcher=request.user) |
#         Q(researchers=request.user)
#     ).distinct()

#     user_accounts = UserBankAccount.objects.filter(user=request.user)
#     bank_choices = UserBankAccount.BANK_CHOICES

#     context = {
#         'form': ResearchApplicationForm(),
#         'researches': researches,
#         'user_accounts': user_accounts,
#         'bank_choices': bank_choices,
#     }
#     return render(request, 'research/application_form.html', context)

# 연구비 신청서 수정
@login_required
def application_edit(request, pk):
    """기존 연구비 신청서를 수정"""
    application = get_object_or_404(ResearchApplication, pk=pk)
    
    # 신청자 본인 또는 관리자만 수정 가능
    if not (request.user == application.applicant or request.user.is_staff):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('research:application_detail', pk=pk)
    
    if request.method == 'POST':
        # 기본 정보 수정
        application.execution_date = request.POST.get('execution_date')
        application.amount = request.POST.get('amount')
        application.description = request.POST.get('description')
        application.budget_subcategory = request.POST.get('budget_subcategory')  # 이 부분 추가
        application.save()
        
        # 지불 방법 수정
        payment_method = PaymentMethod.objects.get(application=application)
        payment_method.is_card = (request.POST.get('payment_type') == 'card')
        payment_method.card_number = request.POST.get('card_number')
        payment_method.bank_name = request.POST.get('bank_name')
        payment_method.account_number = request.POST.get('account_number')
        payment_method.save()
        
        # 새로운 첨부파일 처리
        if request.FILES:
            for file in request.FILES.getlist('attachments'):
                Attachment.objects.create(
                    application=application,
                    file_name=file.name,
                    file=file
                )
        
        messages.success(request, '연구비 신청서가 수정되었습니다.')
        return redirect('research:application_detail', pk=pk)
    
    context = {
        'application': application,
        'payment_method': PaymentMethod.objects.get(application=application),
        'attachments': Attachment.objects.filter(application=application)
    }
    return render(request, 'research/application_form.html', context)

# 첨부파일 삭제
@login_required
def delete_attachment(request, pk):
    """첨부파일 삭제"""
    if request.method == 'POST':
        attachment = get_object_or_404(Attachment, pk=pk)
        application_pk = attachment.application.pk
        
        if request.user == attachment.application.applicant:
            attachment.file.delete()  # 실제 파일 삭제
            attachment.delete()  # DB에서 삭제
            messages.success(request, '첨부파일이 삭제되었습니다.')
            return redirect('research:application_edit', pk=application_pk)
        else:
            messages.error(request, '삭제 권한이 없습니다.')
    
    return redirect('research:application_list')

# 연구비 신청서 상태 변경 (관리자용)
@login_required
@staff_required
def change_application_status(request, pk):
    if request.method == 'POST':
        application = get_object_or_404(ResearchApplication, pk=pk)
        new_status = request.POST.get('status')
        execution_date = request.POST.get('execution_date')
        rejection_reason = request.POST.get('rejection_reason', '')
        
        # '승인'을 '결재'로 매핑
        if new_status == '승인':
            new_status = '결재'
            
        if new_status in ['결재', '기각']:  # 허용된 상태값 명시적 지정
            application.status = new_status
            if new_status == '결재' and execution_date:
                application.execution_date = execution_date
            if new_status == '기각' and rejection_reason:
                application.rejection_reason = rejection_reason
            application.save()
            messages.success(request, f'신청서 상태가 {new_status}(으)로 변경되었습니다.')
        
        return redirect('research:application_detail', pk=pk)
    
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'research/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser:
            return '/admin/'  # superuser는 Django admin으로
        elif self.request.user.is_staff:
            return reverse_lazy('research:staff_dashboard')  # staff는 커스텀 대시보드로
        else:
            return reverse_lazy('research:dashboard')  # 일반 사용자

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('research:login')
    http_method_names = ['post', 'get']  # GET 메소드도 허용

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'research/signup.html'
    success_url = reverse_lazy('research:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '회원가입이 완료되었습니다. 로그인해주세요.')
        return response

    def form_invalid(self, form):
        # 폼 유효성 검사 실패 시 에러 메시지 표시
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form.fields[field].label}: {error}")
        return super().form_invalid(form)

def search_departments(request):
    query = request.GET.get('q', '')
    departments = Department.objects.filter(name__icontains=query).values_list('name', flat=True)
    return JsonResponse(list(departments), safe=False)

@csrf_exempt  # CSRF 토큰 검증 예외 처리
@require_http_methods(["POST"])
def create_department(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        if name:
            # code 필드도 필요하다면 적절한 값을 생성
            code = f"DEPT_{len(Department.objects.all()) + 1}"  # 예시로 간단히 생성
            department = Department.objects.create(name=name, code=code)
            return JsonResponse({'id': department.id, 'name': department.name})
        return JsonResponse({'error': '소속명이 필요합니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
# 관리자 체크 데코레이터
def admin_required(function):
    actual_decorator = user_passes_test(lambda u: u.is_staff)
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required
@admin_required
def admin_dashboard(request):
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 연구과제 통계
    total_research = Research.objects.count()
    active_research = Research.objects.filter(
        contract_from__lte=today.date(),
        contract_to__gte=today.date()
    ).count()
    
    # 연구비 신청 통계
    total_applications = ResearchApplication.objects.count()
    pending_applications = ResearchApplication.objects.filter(status='신청').count()
    
    # 이번 달 통계
    monthly_applications = ResearchApplication.objects.filter(
        application_date__gte=first_day_of_month
    ).count()
    monthly_approved = ResearchApplication.objects.filter(
        application_date__gte=first_day_of_month,
        status='결재'
    ).count()
    
    # 예산 통계
    total_budget = Research.objects.aggregate(
        total=Sum('total_budget')
    )['total'] or 0
    
    used_budget = ResearchApplication.objects.filter(
        status='결재'
    ).aggregate(
        used=Sum('amount')
    )['used'] or 0
    
    # 최근 연구과제
    recent_researches = Research.objects.all().order_by(
        '-created_at'
    )[:5]  # 최근 5개
    
    # 최근 신청
    recent_applications = applications.order_by('-id')[:5]
    
    context = {
        'total_research': total_research,
        'active_research': active_research,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'monthly_applications': monthly_applications,
        'monthly_approved': monthly_approved,
        'total_budget': total_budget,
        'used_budget': used_budget,
        'recent_researches': recent_researches,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'research/admin/dashboard.html', context)

# 연구과제 목록
@login_required
@admin_required
def admin_research_list(request):
    researches = Research.objects.all().order_by('-created_at')
    
    # 검색 필터 적용
    search_query = request.GET.get('search')
    if search_query:
        researches = researches.filter(
            Q(project_number__icontains=search_query) |
            Q(project_name__icontains=search_query) |
            Q(researcher__username__icontains=search_query)
        )
    
    context = {
        'researches': researches
    }
    return render(request, 'research/admin/research_list.html', context)

# 연구과제 생성
@login_required
@admin_required
def admin_research_create(request):
    if request.method == 'POST':
        try:
            # 기본 정보 저장
            research = Research.objects.create(
                project_number=request.POST.get('project_number'),
                project_name=request.POST.get('project_name'),
                researcher_id=request.POST.get('researcher'),
                ordering_organization=request.POST.get('ordering_organization'),
                contract_from=request.POST.get('contract_from'),
                contract_to=request.POST.get('contract_to'),
                total_budget=Decimal(request.POST.get('total_budget', '0'))
            )
            
            # 연구원 추가
            researcher_ids = request.POST.getlist('researchers')
            research.researchers.add(*researcher_ids)
            
            # 예산 항목별 금액 저장
            for budget_type, _ in ResearchBudget.TYPE_CHOICES:
                amount = Decimal(request.POST.get(f'budget_{budget_type}', '0'))
                if amount > 0:
                    ResearchBudget.objects.create(
                        research=research,
                        budget_type=budget_type,
                        total_amount=amount,
                        remaining_amount=amount
                    )
            
            messages.success(request, '연구과제가 성공적으로 등록되었습니다.')
            return redirect('research:admin_research_detail', pk=research.pk)
            
        except Exception as e:
            messages.error(request, f'연구과제 등록 중 오류가 발생했습니다: {str(e)}')
            return redirect('research:admin_research_create')
    
    # GET 요청 처리
    context = {
        'users': User.objects.all(),
        'budget_types': ResearchBudget.TYPE_CHOICES,
    }
    return render(request, 'research/admin/research_create.html', context)

# 연구과제 상세 정보
@login_required
@admin_required
def admin_research_detail(request, pk):
    research = get_object_or_404(Research, pk=pk)
    budgets = research.budgets.all()
    applications = ResearchApplication.objects.filter(research_budget__research=research)
    
    context = {
        'research': research,
        'budgets': budgets,
        'applications': applications,
    }
    return render(request, 'research/admin/research_detail.html', context)

# 연구과제 수정
@login_required
@admin_required
def admin_research_edit(request, pk):
    research = get_object_or_404(Research, pk=pk)
    
    if request.method == 'POST':
        try:
            # 기본 정보 수정
            research.project_name = request.POST.get('project_name')
            research.ordering_organization = request.POST.get('ordering_organization')
            research.contract_from = request.POST.get('contract_from')
            research.contract_to = request.POST.get('contract_to')
            research.total_budget = Decimal(request.POST.get('total_budget', '0'))
            research.save()
            
            # 연구원 수정
            research.researchers.clear()
            researcher_ids = request.POST.getlist('researchers')
            research.researchers.add(*researcher_ids)
            
            # 예산 항목 수정
            for budget_type, _ in ResearchBudget.TYPE_CHOICES:
                amount = Decimal(request.POST.get(f'budget_{budget_type}', '0'))
                budget = research.budgets.filter(budget_type=budget_type).first()
                
                if amount > 0:
                    if budget:
                        budget.total_amount = amount
                        budget.remaining_amount = amount
                        budget.save()
                    else:
                        ResearchBudget.objects.create(
                            research=research,
                            budget_type=budget_type,
                            total_amount=amount,
                            remaining_amount=amount
                        )
                elif budget:
                    budget.delete()
            
            messages.success(request, '연구과제가 성공적으로 수정되었습니다.')
            return redirect('research:admin_research_detail', pk=research.pk)
            
        except Exception as e:
            messages.error(request, f'연구과제 수정 중 오류가 발생했습니다: {str(e)}')
    
    context = {
        'research': research,
        'users': User.objects.all(),
        'budget_types': ResearchBudget.TYPE_CHOICES,
    }
    return render(request, 'research/admin/research_edit.html', context)

# 연구과제 삭제
@login_required
@admin_required
def admin_research_delete(request, pk):
    if request.method == 'POST':
        research = get_object_or_404(Research, pk=pk)
        try:
            research.delete()
            messages.success(request, '연구과제가 성공적으로 삭제되었습니다.')
            return redirect('research:admin_research_list')
        except Exception as e:
            messages.error(request, f'연구과제 삭제 중 오류가 발생했습니다: {str(e)}')
            return redirect('research:admin_research_detail', pk=pk)
    
    return redirect('research:admin_research_list')

# 연구비 신청 관리 뷰들
@login_required
@admin_required
def admin_application_list(request):
    applications = ResearchApplication.objects.all().order_by('-application_date')
    
    # 검색 필터 적용
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project_number = request.GET.get('project_number')
    status = request.GET.get('status')
    applicant = request.GET.get('applicant')
    budget_type = request.GET.get('budget_type')

    if start_date and end_date:
        applications = applications.filter(application_date__range=[start_date, end_date])
    if project_number:
        applications = applications.filter(research_budget__research__project_number__icontains=project_number)
    if status:
        applications = applications.filter(status=status)
    if applicant:
        applications = applications.filter(
            Q(applicant__username__icontains=applicant) |
            Q(applicant__first_name__icontains=applicant)
        )
    if budget_type:
        applications = applications.filter(research_budget__budget_type=budget_type)

    context = {
        'applications': applications,
        'status_choices': ResearchApplication.STATUS_CHOICES,
        'budget_types': ResearchBudget.TYPE_CHOICES
    }
    return render(request, 'research/admin/application_list.html', context)

@login_required
@admin_required
def admin_application_detail(request, pk):
    application = get_object_or_404(ResearchApplication, pk=pk)
    attachments = application.attachment_set.all()
    
    context = {
        'application': application,
        'attachments': attachments,
        'status_choices': ResearchApplication.STATUS_CHOICES
    }
    return render(request, 'research/admin/application_detail.html', context)

@login_required
@admin_required
def admin_application_status_change(request, pk):
    if request.method == 'POST':
        application = get_object_or_404(ResearchApplication, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(ResearchApplication.STATUS_CHOICES):
            old_status = application.status
            application.status = new_status
            application.save()
            
            # 만약 승인 상태로 변경되면 예산 차감
            if new_status == '결재' and old_status != '결재':
                budget = application.research_budget
                budget.remaining_amount -= application.amount
                budget.save()
            
            messages.success(request, f'신청서 상태가 {new_status}(으)로 변경되었습니다.')
        
        return redirect('research:admin_application_detail', pk=pk)
    
    return redirect('research:admin_application_list')

@login_required
@admin_required
def admin_application_reject(request, pk):
    if request.method == 'POST':
        application = get_object_or_404(ResearchApplication, pk=pk)
        rejection_reason = request.POST.get('rejection_reason')
        
        application.status = '기각'
        application.rejection_reason = rejection_reason
        application.save()
        
        messages.success(request, '신청서가 기각되었습니다.')
        return redirect('research:admin_application_detail', pk=pk)
    
    return redirect('research:admin_application_list')

# 엑셀 다운로드 뷰들
@login_required
@admin_required
def admin_application_excel(request):
    # 검색 조건 적용
    applications = ResearchApplication.objects.all().order_by('-application_date')
    
    # BytesIO 객체를 생성하여 메모리에 엑셀 파일 저장
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # 헤더 스타일 설정
    header_style = workbook.add_format({
        'bold': True,
        'align': 'center',
        'bg_color': '#4472C4',
        'font_color': 'white'
    })

    # 헤더 작성
    headers = [
        '신청번호', '상태', '신청일자', '과제번호', '과제명', '신청자', 
        '예산항목', '신청금액', '집행일자', '기각사유'
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_style)

    # 데이터 작성
    for row, app in enumerate(applications, 1):
        worksheet.write(row, 0, app.application_number)
        worksheet.write(row, 1, app.get_status_display())
        worksheet.write(row, 2, app.application_date.strftime('%Y-%m-%d'))
        worksheet.write(row, 3, app.research_budget.research.project_number)
        worksheet.write(row, 4, app.research_budget.research.project_name)
        worksheet.write(row, 5, app.applicant.get_full_name())
        worksheet.write(row, 6, app.research_budget.get_budget_type_display())
        worksheet.write(row, 7, float(app.amount))
        worksheet.write(row, 8, app.execution_date.strftime('%Y-%m-%d'))
        worksheet.write(row, 9, app.rejection_reason or '')

    # 열 너비 자동 조정
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, len(header) * 2)

    workbook.close()
    
    # 파일 다운로드 응답 생성
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=applications_{}.xlsx'.format(
        datetime.now().strftime('%Y%m%d')
    )
    
    return response

@login_required
@admin_required
def admin_research_excel(request):
    researches = Research.objects.all().order_by('-created_at')
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # 헤더 스타일 설정
    header_style = workbook.add_format({
        'bold': True,
        'align': 'center',
        'bg_color': '#4472C4',
        'font_color': 'white'
    })

    # 헤더 작성
    headers = [
        '과제번호', '과제명', '연구책임자', '발주기관', 
        '계약시작일', '계약종료일', '총예산', '생성일시'
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_style)

    # 데이터 작성
    for row, research in enumerate(researches, 1):
        worksheet.write(row, 0, research.project_number)
        worksheet.write(row, 1, research.project_name)
        worksheet.write(row, 2, research.researcher.get_full_name())
        worksheet.write(row, 3, research.ordering_organization)
        worksheet.write(row, 4, research.contract_from.strftime('%Y-%m-d'))
        worksheet.write(row, 5, research.contract_to.strftime('%Y-%m-d'))
        worksheet.write(row, 6, float(research.total_budget))
        worksheet.write(row, 7, research.created_at.strftime('%Y-%m-%d %H:%M:%S'))

    # 열 너비 자동 조정
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, len(header) * 2)

    workbook.close()
    
    # 파일 다운로드 응답 생성
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=researches_{}.xlsx'.format(
        datetime.now().strftime('%Y%m%d')
    )
    
    return response

@login_required
def get_research_info(request, research_id):
    """연구과제 정보를 JSON으로 반환하는 API"""
    from django.db import connection
    
    try:
        research = get_object_or_404(
            Research.objects.select_related(
                'researcher',
                'researcher__department'
            ), 
            id=research_id
        )

        # 디버깅: 현재 연구책임자의 정보 출력
        print(f"Researcher ID: {research.researcher.id}")
        print(f"Researcher Username: {research.researcher.username}")
        print(f"Researcher Department ID: {research.researcher.department_id}")
        
        # SQL 쿼리로 직접 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.name 
                FROM research_department d 
                JOIN research_user u ON u.department_id = d.id 
                WHERE u.military_id = %s
            """, [research.researcher.military_id])
            department_name = cursor.fetchone()
            print(f"Department from SQL: {department_name}")

        # 각 예산 항목별로 남은 잔액 재계산
        budget_items = []
        for budget in research.budgets.all():
            # 해당 예산 항목의 '신청' 또는 '결재' 상태인 신청금액 합계 계산
            from django.db.models import Sum
            used_amount = ResearchApplication.objects.filter(
                research_budget=budget,
                status__in=['신청', '결재']
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # 잔액 업데이트
            budget.remaining_amount = budget.total_amount - used_amount
            budget.save()
            
            budget_items.append({
                'id': budget.id,
                'type': budget.get_budget_type_display(),
                'total_amount': float(budget.total_amount),
                'remaining_amount': float(budget.remaining_amount)
            })

        researcher_data = {
            'name': research.researcher.get_full_name(),
            'id': research.researcher.username,
            'department': department_name[0] if department_name else ''  # SQL 결과 사용
        }

        data = {
            'researcher': researcher_data,
            'total_budget': float(research.total_budget),
            'budget_items': budget_items
        }
        return JsonResponse(data)
        
    except Exception as e:
        print(f"Error in get_research_info: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def search_research(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', '')  # 'number' 또는 'name'
    
    if search_type == 'number':
        researches = Research.objects.filter(project_number__icontains=query)
    else:  # name
        researches = Research.objects.filter(project_name__icontains=query)
    
    results = [{
        'id': r.id,
        'project_number': r.project_number,
        'project_name': r.project_name
    } for r in researches]
    
    return JsonResponse({'results': results})

@login_required
@require_POST
def delete_applications(request):
    application_ids = request.POST.getlist('selected_applications')
    
    if not application_ids:
        messages.error(request, '삭제할 항목을 선택해주세요.')
        return redirect('research:dashboard')
    
    # 권한 확인 (본인이 신청한 것만 삭제 가능)
    applications = ResearchApplication.objects.filter(
        id__in=application_ids,
        applicant=request.user  # 본인이 신청한 것만
    )
    
    deleted_count = applications.count()
    applications.delete()
    
    messages.success(request, f'{deleted_count}개의 연구비신청이 삭제되었습니다.')
    return redirect('research:dashboard')

@require_http_methods(["GET"])
def get_budget_subcategories(request):
    category = request.GET.get('category', '')
    subcategories = {
        '인건비': ['외부인건비', '용역', '학생인건비'],
        '연구수당': ['연구수당'],
        '연구시설/장비비': [
            '기기/장비구입', '사무기기/비품구입', '전산처리/관리비용', '소프트웨어 구입', 
            '시약/재료구입', '시제품/시험설비 제작', '장비사용료', '유지보수비', '임차료', 
            '분석료', '시설/장비구입', '운영비', '개발경비', '연구 인프라 조성 경비', '기타', '기타재료비'
        ],
        '연구활동비': [
            '국외여비', '인쇄/복사/인화/슬라이드 제작', '공공요금', '제세공과금', 
            '기술/특허정보수집비용', '학회/세미나 참가비', '세미나개최비', '전문가활용비', 
            '원고료/통역료', '풍동사용료', '실험비용', '임대료', '문헌구입비', 
            '연구서비스활용비', '학회등록비', '논문심사비', '국내여비', '사무기기/비품구입', 
            '소프트웨어 구입', '사무용품', '회의비', '야근식대', '우편요금/택배비/수수료', 
            '교육훈련', '회의장 사용', '기타', '기타수수료'
        ],
        '연구재료비': [
            '국내여비', '사무용품', '회의비', '야근식대', '전산처리/관리비용', 
            '시약/재료구입', '시제품/시험설비 제작', '기타'
        ],
        '간접비': ['연구자원관리비', '기타'],
        '통장이자': ['-'],
        '위탁연구개발비': ['위탁연구개발비'],
        '보안수당': ['보안수당'],
        '연구윤리활동비': ['연구윤리활동비'],
        '연구실안전관리비': ['연구실안전관리비']
    }
    
    return JsonResponse({
        'subcategories': subcategories.get(category, [])
    })

@login_required
@require_http_methods(["POST"])
def create_bank_account(request):
    try:
        data = json.loads(request.body)
        account = UserBankAccount.objects.create(
            user=request.user,
            bank_name=data['bank_name'],
            account_number=data['account_number'],
            account_holder=data['account_holder']
        )
        
        # 사용자의 첫 계좌라면 기본계좌로 설정
        if UserBankAccount.objects.filter(user=request.user).count() == 1:
            account.is_default = True
            account.save()
        
        return JsonResponse({
            'id': account.id,
            'bank_name': account.bank_name,
            'account_number': account.account_number,
            'account_holder': account.account_holder
        })
    except Exception as e:
        return JsonResponse({
            'message': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def create_research_card(request):
    try:
        data = json.loads(request.body)
        research = Research.objects.get(id=data['research_id'])
        
        # 이미 존재하는 카드인지 확인
        existing_card = ResearchCard.objects.filter(
            research=research,
            card_number=data['card_number']
        ).first()
        
        if existing_card:
            if not existing_card.is_active:
                # 비활성화된 카드를 다시 활성화
                existing_card.is_active = True
                existing_card.save()
                return JsonResponse({
                    'id': existing_card.id,
                    'card_number': existing_card.card_number
                })
            else:
                return JsonResponse({
                    'message': '이미 등록된 카드번호입니다.'
                }, status=400)
        
        # 새 카드 생성
        card = ResearchCard.objects.create(
            research=research,
            card_number=data['card_number']
        )
        
        return JsonResponse({
            'id': card.id,
            'card_number': card.card_number
        })
        
    except Research.DoesNotExist:
        return JsonResponse({
            'message': '연구과제를 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'message': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def get_user_accounts(request):
    accounts = UserBankAccount.objects.filter(user=request.user)
    return JsonResponse({
        'accounts': [{
            'id': account.id,
            'bank_name': account.bank_name,
            'account_number': account.account_number,
            'account_holder': account.account_holder,
            'is_default': account.is_default
        } for account in accounts]
    })

@login_required
@require_http_methods(["GET"])
def get_research_cards(request, research_id):
    try:
        research = Research.objects.get(id=research_id)
        cards = ResearchCard.objects.filter(
            research=research,
            is_active=True
        ).order_by('-created_at')  # 최근 등록된 카드부터 표시
        
        return JsonResponse({
            'cards': [{
                'id': card.id,
                'card_number': card.card_number
            } for card in cards]
        })
    except Research.DoesNotExist:
        return JsonResponse({
            'message': '연구과제를 찾을 수 없습니다.'
        }, status=404)

# application_create view 수정
@login_required
def application_create(request):
    if request.method == 'POST':
        form = ResearchApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.status = '신청'
            application.save()

            # 지불 방법 처리
            payment_type = request.POST.get('payment_type')
            payment_method = PaymentMethod(
                application=application,
                is_card=(payment_type == 'card')
            )
            
            if payment_type == 'card':
                payment_method.card_id = request.POST.get('card')
            else:
                payment_method.bank_account_id = request.POST.get('bank_account')
            
            payment_method.save()

            # 첨부파일 처리
            for file in request.FILES.getlist('attachments'):
                Attachment.objects.create(
                    application=application,
                    file_name=file.name,
                    file=file
                )

            messages.success(request, '연구비 신청이 완료되었습니다.')
            return redirect('research:application_detail', pk=application.pk)

        # 폼이 유효하지 않을 경우, 에러 메시지를 전달
        context = {
            'form': form,
            'errors': form.errors,
            'user_accounts': UserBankAccount.objects.filter(user=request.user),
            'bank_choices': UserBankAccount.BANK_CHOICES,
        }
        return render(request, 'research/application_form.html', context)
    
    # GET 요청 처리
    researches = Research.objects.filter(
        Q(researcher=request.user) |
        Q(researchers=request.user)
    ).distinct()

    user_accounts = UserBankAccount.objects.filter(user=request.user)
    bank_choices = UserBankAccount.BANK_CHOICES

    context = {
        'form': ResearchApplicationForm(),
        'researches': researches,
        'user_accounts': user_accounts,
        'bank_choices': bank_choices,
    }
    return render(request, 'research/application_form.html', context)

# 관리자 신청 폼
def staff_request(request):
    if request.method == 'POST':
        form = StaffRequestForm(request.POST)
        if form.is_valid():
            staff_request = form.save(commit=False)
            if request.user.is_authenticated:
                staff_request.user = request.user
            staff_request.save()
            messages.success(request, '관리자 신청이 완료되었습니다. 승인을 기다려주세요.')
            return redirect('research:login')
    else:
        form = StaffRequestForm()
    
    context = {'form': form}
    return render(request, 'research/staff_request.html', context)

# 관리자 신청 목록 (superuser용)
@user_passes_test(lambda u: u.is_superuser)
def staff_request_list(request):
    status_filter = request.GET.get('status', '')
    staff_requests = StaffRequest.objects.all()
    
    if status_filter:
        staff_requests = staff_requests.filter(status=status_filter)

    context = {
        'staff_requests': staff_requests,
    }
    return render(request, 'research/staff/staff_request_list.html', context)

# 관리자 신청 상세 정보 API
@user_passes_test(lambda u: u.is_superuser)
def staff_request_detail(request, pk):
    try:
        staff_request = StaffRequest.objects.get(pk=pk)
        data = {
            'reason': staff_request.reason,
            'status': staff_request.status,
            'rejection_reason': staff_request.rejection_reason,
            'created_at': staff_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'name': staff_request.user.get_full_name(),
                'department': staff_request.user.department.name if staff_request.user.department else '',
                'status': staff_request.user.get_status_display(),
            }
        }
        return JsonResponse(data)
    except StaffRequest.DoesNotExist:
        return JsonResponse({'error': '요청을 찾을 수 없습니다.'}, status=404)

# 관리자 신청 승인 API
@user_passes_test(lambda u: u.is_superuser)
def staff_request_approve(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=405)
    
    try:
        staff_request = StaffRequest.objects.get(pk=pk)
        
        if staff_request.status != 'pending':
            return JsonResponse({'error': '이미 처리된 요청입니다.'}, status=400)

        # 새로운 staff 계정 생성
        user = User.objects.create_user(
            username=staff_request.desired_username,
            password=staff_request.password,
            is_staff=True
        )
        
        # 신청 상태 업데이트
        staff_request.status = 'approved'
        staff_request.reviewed_at = timezone.now()
        staff_request.reviewed_by = request.user
        staff_request.save()
        
        messages.success(request, f'관리자 계정이 생성되었습니다.')
        return JsonResponse({'status': 'success'})
        
    except StaffRequest.DoesNotExist:
        return JsonResponse({'error': '요청을 찾을 수 없습니다.'}, status=404)

# 관리자 신청 거절 API
@user_passes_test(lambda u: u.is_superuser)
def staff_request_reject(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=405)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason')
        
        if not reason:
            return JsonResponse({'error': '거절 사유를 입력해주세요.'}, status=400)
        
        staff_request = StaffRequest.objects.get(pk=pk)
        
        # 이미 처리된 요청인지 확인
        if staff_request.status != 'pending':
            return JsonResponse({'error': '이미 처리된 요청입니다.'}, status=400)
        
        # 신청 상태 업데이트
        staff_request.status = 'rejected'
        staff_request.rejection_reason = reason
        staff_request.reviewed_at = timezone.now()
        staff_request.reviewed_by = request.user
        staff_request.save()
        
        messages.success(request, f'{staff_request.user.get_full_name()}님의 관리자 신청이 거절되었습니다.')
        return JsonResponse({'status': 'success'})
        
    except StaffRequest.DoesNotExist:
        return JsonResponse({'error': '요청을 찾을 수 없습니다.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    
@staff_required
def staff_application_excel(request):
    if request.method != 'POST':
        return redirect('research:staff_application_list')

    selected_ids = request.POST.getlist('selected_applications')
    if not selected_ids:
        messages.error(request, '선택된 연구비 신청이 없습니다!')
        return redirect('research:staff_application_list')

    applications = ResearchApplication.objects.filter(id__in=selected_ids)
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    header_style = workbook.add_format({
        'bold': True,
        'align': 'center',
        'bg_color': '#4472C4',
        'font_color': 'white'
    })

    # 헤더 수정: 신청번호 제거, 연구비항목 추가
    headers = [
        '상태', '신청일자', '과제번호', '과제명', '신청자', 
        '예산항목', '연구비항목', '신청금액', '집행일자', '기각사유'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_style)

    for row, app in enumerate(applications, 1):
        worksheet.write(row, 0, app.get_status_display())  # 상태
        worksheet.write(row, 1, app.application_date.strftime('%Y-%m-%d'))  # 신청일자
        worksheet.write(row, 2, app.research_budget.research.project_number)  # 과제번호
        worksheet.write(row, 3, app.research_budget.research.project_name)  # 과제명
        worksheet.write(row, 4, app.applicant.get_full_name())  # 신청자
        worksheet.write(row, 5, app.research_budget.get_budget_type_display())  # 예산항목
        worksheet.write(row, 6, app.budget_subcategory)  # 연구비항목 추가
        worksheet.write(row, 7, float(app.amount))  # 신청금액
        worksheet.write(row, 8, app.execution_date.strftime('%Y-%m-%d') if app.execution_date else '')  # 집행일자
        worksheet.write(row, 9, app.rejection_reason or '')  # 기각사유

    for i, _ in enumerate(headers):
        worksheet.set_column(i, i, 15)  # 각 열의 너비를 15로 설정

    workbook.close()
    
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=applications_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    return response

@staff_required
def staff_application_view(request, pk):
    application = get_object_or_404(ResearchApplication, pk=pk)
    attachments = application.attachment_set.all()
    payment_method = PaymentMethod.objects.filter(application=application).first()
    
    context = {
        'application': application,
        'attachments': attachments,
        'payment_method': payment_method,
        'status_choices': ResearchApplication.STATUS_CHOICES
    }
    return render(request, 'research/staff/application_detail.html', context)

@staff_required
def staff_research_create(request):
    if request.method == 'POST':
        form = ResearchForm(request.POST)
        if form.is_valid():
            research = form.save(commit=False)
            
            # 연구책임자 설정
            researcher_id = request.POST.get('researcher')
            if researcher_id:
                research.researcher_id = researcher_id
            
            research.save()
            
            # 연구원 설정
            researchers = request.POST.get('researchers')
            if researchers:
                researcher_ids = json.loads(researchers)
                research.researchers.set(researcher_ids)
            
            # ResearchBudget 처리
            budget_formset = ResearchBudgetFormSet(request.POST, instance=research)
            if budget_formset.is_valid():
                budget_formset.save()
                messages.success(request, '연구과제가 성공적으로 생성되었습니다.')
                return redirect('research:staff_research_list')
            else:
                research.delete()
                messages.error(request, '예산 정보에 오류가 있습니다.')
        else:
            messages.error(request, '입력 정보에 오류가 있습니다.')
    else:
        form = ResearchForm()
        budget_formset = ResearchBudgetFormSet()
    
    context = {
        'form': form,
        'budget_formset': budget_formset,
        'budget_types': ResearchBudget.TYPE_CHOICES,
    }
    return render(request, 'research/staff/research_create.html', context)

@staff_required
def search_users(request):
    query = request.GET.get('q', '')
    
    # staff나 superuser가 아닌 일반 User만 검색
    users = User.objects.filter(
        is_staff=False, 
        is_superuser=False
    ).select_related('department')  # department 정보를 함께 가져옴
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |  # ID로 검색
            Q(first_name__icontains=query)   # 이름으로 검색
        )
    
    users_data = [{
        'id': str(user.id),
        'username': user.username,
        'name': user.get_full_name(),
        'department': user.department.name if user.department else '소속 없음'
    } for user in users[:10]]  # 최대 10명까지만 반환
    
    return JsonResponse({'users': users_data})