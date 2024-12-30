from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    # 기존 URL 패턴들
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('applications/', views.application_list, name='application_list'),
    path('application/new/', views.application_create, name='application_create'),
    path('application/<int:pk>/', views.application_detail, name='application_detail'),
    path('application/<int:pk>/edit/', views.application_edit, name='application_edit'),
    path('attachment/<int:pk>/delete/', views.delete_attachment, name='delete_attachment'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('api/get-research-cards/<int:research_id>/', views.get_research_cards, name='get_research_cards'),
    path('staff/research/new/', views.staff_research_create, name='staff_research_create'),
    path('research/api/search-users/', views.search_users, name='search_users'),

    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/research/', views.staff_research_list, name='staff_research_list'),
    path('staff/applications/', views.staff_application_list, name='staff_application_list'),
    # 관리자 신청 관련 URL
    path('staff-request/', views.staff_request, name='staff_request'),
    path('staff/request-list/', views.staff_request_list, name='staff_request_list'),
    
    # 관리자 신청 API URL
    path('api/staff-requests/<int:pk>/', views.staff_request_detail, name='staff_request_detail'),
    path('api/staff-requests/<int:pk>/approve/', views.staff_request_approve, name='staff_request_approve'),
    path('api/staff-requests/<int:pk>/reject/', views.staff_request_reject, name='staff_request_reject'),
    
    path('api/departments/search/', views.search_departments, name='search_departments'),
    path('api/departments/create/', views.create_department, name='create_department'),
    path('api/research/search/', views.search_research, name='search_research'),
    path('applications/delete/', views.delete_applications, name='delete_applications'),
    path('api/get-budget-subcategories/', views.get_budget_subcategories, name='get_budget_subcategories'),
    path('api/bank-accounts/', views.create_bank_account, name='create_bank_account'),
    path('api/research-cards/', views.create_research_card, name='create_research_card'),
    path('api/user-accounts/', views.get_user_accounts, name='get_user_accounts'),
    path('api/research-cards/<int:research_id>/', views.get_research_cards, name='get_research_cards'),
    path('application/<int:pk>/status/', views.change_application_status, name='change_application_status'),

    # API 경로 추가
    path('api/research-info/<int:research_id>/', views.get_research_info, name='research_info'),

    # 관리자용 URL 패턴 추가
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # 연구과제 관리
    path('admin/research/', views.admin_research_list, name='admin_research_list'),
    path('admin/research/new/', views.admin_research_create, name='admin_research_create'),
    path('admin/research/<int:pk>/', views.admin_research_detail, name='admin_research_detail'),
    path('admin/research/<int:pk>/edit/', views.admin_research_edit, name='admin_research_edit'),
    path('admin/research/<int:pk>/delete/', views.admin_research_delete, name='admin_research_delete'),
    
    # 연구비 신청 관리
    path('staff/applications/', views.staff_application_list, name='staff_application_list'), 
    path('staff/application/<int:pk>/', views.staff_application_view, name='staff_application_view'),
    path('admin/application/<int:pk>/status/', views.admin_application_status_change, name='admin_application_status_change'),
    path('admin/application/<int:pk>/reject/', views.admin_application_reject, name='admin_application_reject'),
    
    # 엑셀 다운로드
    path('staff/excel/', views.staff_application_excel, name='staff_excel'),
    path('admin/research/excel/', views.admin_research_excel, name='admin_research_excel'),
]