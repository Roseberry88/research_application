#views.py 에
@login_required
def dashboard(request):
    """사용자의 연구비 신청 현황을 보여주는 대시보드"""
    recent_applications = ResearchApplication.objects.filter(
        applicant=request.user
    ).order_by('-application_date')[:5]
    
    total_budget = ResearchBudget.objects.filter(
        researcher=request.user
    ).count()
    
    pending_applications = ResearchApplication.objects.filter(
        applicant=request.user,
        status='신청'
    ).count()
    
    context = {
        'recent_applications': recent_applications,
        'total_budget': total_budget,
        'pending_applications': pending_applications
    }
    return render(request, 'research/dashboard.html', context)

#dashboard.html에
{% extends 'research/base.html' %}

{% block content %}
<div class="bg-white shadow rounded-lg p-6">
    <h2 class="text-2xl font-bold mb-6">대시보드</h2>
    
    <!-- 통계 카드 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="bg-blue-50 p-4 rounded-lg">
            <h3 class="text-lg font-semibold text-blue-900">전체 연구과제</h3>
            <p class="text-3xl font-bold text-blue-600">{{ total_budget }}</p>
        </div>
        <div class="bg-yellow-50 p-4 rounded-lg">
            <h3 class="text-lg font-semibold text-yellow-900">대기중인 신청</h3>
            <p class="text-3xl font-bold text-yellow-600">{{ pending_applications }}</p>
        </div>
        <div class="bg-green-50 p-4 rounded-lg">
            <h3 class="text-lg font-semibold text-green-900">최근 승인된 신청</h3>
            <p class="text-3xl font-bold text-green-600">{{ recent_approved }}</p>
        </div>
    </div>

    <!-- 최근 신청 목록 -->
    <div class="mt-8">
        <h3 class="text-xl font-semibold mb-4">최근 신청 내역</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신청일자</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">과제번호</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">과제명</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">금액</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {% for application in recent_applications %}
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap">{{ application.application_date }}</td>
                        <td class="px-6 py-4 whitespace-nowrap">{{ application.research_budget.project_number }}</td>
                        <td class="px-6 py-4">
                            <a href="{% url 'research:application_detail' application.pk %}" 
                               class="text-blue-600 hover:text-blue-900">
                                {{ application.research_budget.project_name }}
                            </a>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">{{ application.amount|floatformat:0 }}원</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                       {% if application.status == '승인' %}bg-green-100 text-green-800
                                       {% elif application.status == '반려' %}bg-red-100 text-red-800
                                       {% else %}bg-yellow-100 text-yellow-800{% endif %}">
                                {{ application.status }}
                            </span>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                            최근 신청 내역이 없습니다.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}