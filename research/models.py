from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    last_name = None

    RANK_CHOICES = [
       ('교수', '교수'),
       ('부교수', '부교수'), 
       ('조교수', '조교수'),
       ('강사', '강사'),
       ('이등병', '이등병'),
       ('일병', '일병'),
       ('상병', '상병'),
       ('병장', '병장'),
       ('하사', '하사'),
       ('중사', '중사'), 
       ('상사', '상사'),
       ('원사', '원사'),
       ('준위', '준위'),
       ('소위', '소위'),
       ('중위', '중위'),
       ('대위', '대위'),
       ('소령', '소령'),
       ('중령', '중령'),
       ('대령', '대령'),
       # 수식어가 포함된 계급
       ('대령(진)', '대령(진)'),
       ('대령(임)', '대령(임)'),
       ('중령(진)', '중령(진)'),
       ('중령(임)', '중령(임)'),
       ('소령(진)', '소령(진)'),
       ('소령(임)', '소령(임)'),
       ('대위(진)', '대위(진)'),
       ('대위(임)', '대위(임)'),
       ('중위(진)', '중위(진)'),
       ('중위(임)', '중위(임)'),
       ('소위(진)', '소위(진)'),
       ('소위(임)', '소위(임)'),
       ('원사(진)', '원사(진)'),
       ('원사(임)', '원사(임)'),
       ('상사(진)', '상사(진)'),
       ('상사(임)', '상사(임)'),
       ('중사(진)', '중사(진)'),
       ('중사(임)', '중사(임)'),
       ('하사(진)', '하사(진)'),
       ('하사(임)', '하사(임)'),
    ]

    STATUS_CHOICES = [
        ('군무원', '군무원'),
        ('생도', '생도'),
        ('민간인', '민간인'),
        ('현역', '현역'),
        ('연구원', '연구원'),
        ('예비역', '예비역'),
        ('조교수', '조교수'),
        ('학생연구원', '학생연구원'),
    ]

    POSITION_CHOICES = [
        ('교수', '교수'),
        ('부교수', '부교수'),
        ('조교수(전임)', '조교수(전임)'),
        ('조교수(일반)', '조교수(일반)'),
        ('군교관', '군교관'),
        ('강사', '강사'),
        ('외래강사', '외래강사'),
    ]

    APPROVAL_CHOICES = [
        ('산학협력팀장', '산학협력팀장'),
        ('과제운영팀장', '과제운영팀장'),
    ]
    
    military_id = models.CharField(max_length=10, unique=True, verbose_name='군번')
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, null=True, blank=True, verbose_name='계급')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, verbose_name='소속')

    # 새로운 필드들 추가
    internal_external = models.CharField(
        max_length=10, 
        choices=[('internal', '내부'), ('external', '외부')],
        verbose_name='내/외부구분'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='신분구분'
    )
    
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        null=True,
        blank=True,
        verbose_name='직위'
    )
    
    approval_authority = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        null=True,
        blank=True,
        verbose_name='결재권한'
    )

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def get_full_name(self):
        """
        사용자의 이름만 반환
        """
        return self.first_name.strip()
    
class BudgetCategory(models.Model):
    TYPE_CHOICES = [
        ('인건비', '인건비'),
        ('연구수당', '연구수당'),
        ('연구시설/장비비', '연구시설/장비비'),
        ('연구활동비', '연구활동비'),
        ('연구재료비', '연구재료비'),
        ('간접비', '간접비'),
        ('통장이자', '통장이자'),
        ('위탁연구개발비', '위탁연구개발비'),
        ('보안수당', '보안수당'),
        ('연구윤리활동비', '연구윤리활동비'),
        ('연구실안전관리비', '연구실안전관리비'),
    ]
    
    name = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name='예산항목')
    
    class Meta:
        verbose_name = '예산항목'
        verbose_name_plural = '예산항목 목록'

    def __str__(self):
        return self.get_name_display()
    
class BudgetSubCategory(models.Model):
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE, related_name='subcategories', verbose_name='예산항목')
    name = models.CharField(max_length=100, verbose_name='연구비항목')
    
    class Meta:
        verbose_name = '연구비항목'
        verbose_name_plural = '연구비항목 목록'

    def __str__(self):
        return f"{self.category.get_name_display()} - {self.name}"

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name='학과명')
    code = models.CharField(max_length=20, verbose_name='학과코드')
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '학과'
        verbose_name_plural = '학과 목록'

# models.py에 추가할 내용

class Research(models.Model):
    project_number = models.CharField(max_length=20, unique=True, verbose_name='과제번호')
    project_name = models.CharField(max_length=200, verbose_name='과제명')
    researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='research_projects',
        verbose_name='연구책임자'
    )
    researchers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='participating_projects',
        verbose_name='연구원',
        blank=True
    )
    ordering_organization = models.CharField(max_length=100, verbose_name='발주기관')
    contract_from = models.DateField(verbose_name='계약시작일')
    contract_to = models.DateField(verbose_name='계약종료일')
    total_budget = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name='연구비 총액'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '연구과제'
        verbose_name_plural = '연구과제 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project_number} - {self.project_name}"

    def get_total_budget_display(self):
        return f"{self.total_budget:,}원"

    def get_contract_period_display(self):
        return f"{self.contract_from} ~ {self.contract_to}"

    def is_active(self):
        today = timezone.now().date()
        return self.contract_from <= today <= self.contract_to

# ResearchBudget 모델 수정
class ResearchBudget(models.Model):
    TYPE_CHOICES = [
        ('인건비', '인건비'),
        ('연구수당', '연구수당'),
        ('연구시설/장비비', '연구시설/장비비'),
        ('연구활동비', '연구활동비'),
        ('연구재료비', '연구재료비'),
        ('간접비', '간접비'),
        ('통장이자', '통장이자'),
        ('위탁연구개발비', '위탁연구개발비'),
        ('보안수당', '보안수당'),
        ('연구윤리활동비', '연구윤리활동비'),
        ('연구실안전관리비', '연구실안전관리비'),
    ]

    research = models.ForeignKey(
        'Research',
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='연구과제'
    )
    budget_type = models.CharField(
        max_length=50, 
        choices=TYPE_CHOICES, 
        verbose_name='예산항목'
    )
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        verbose_name='예산액'
    )
    remaining_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        verbose_name='잔액'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='생성일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='수정일시'
    )
    
    class Meta:
        verbose_name = '연구예산'
        verbose_name_plural = '연구예산 목록'
        unique_together = ['research', 'budget_type']
    
    def __str__(self):
        return f"{self.research.project_name} - {self.get_budget_type_display()}"

    def save(self, *args, **kwargs):
        if self._state.adding:  # 새로운 객체 생성시
            self.remaining_amount = self.total_amount
        super().save(*args, **kwargs)

    def get_usage_percentage(self):
        if self.total_amount == 0:
            return 0
        return round((1 - (self.remaining_amount / self.total_amount)) * 100, 2)
    
    def calculate_remaining_amount(self):
        """해당 예산 항목의 잔액을 계산합니다"""
        from django.db.models import Sum
        
        # 현재 진행중인 신청금액 합계 계산
        used_amount = ResearchApplication.objects.filter(
            research_budget=self,
            status__in=['신청', '결재']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return self.total_amount - used_amount

    def update_remaining_amount(self):
        self.remaining_amount = self.calculate_remaining_amount()
        self.save()

    def get_total_research_budget(self):
        """연구비 총액: 모든 예산항목의 합계를 반환"""
        return self.research.budgets.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    def get_budget_amount(self):
        """예산: 해당 예산항목에 배정된 예산"""
        return self.total_amount

class ResearchApplication(models.Model):
    STATUS_CHOICES = [
        ('신청', '신청'),
        ('결재', '결재'),
        ('기각', '기각'),
    ]
    
    application_number = models.CharField(max_length=20, verbose_name='신청번호')
    research_budget = models.ForeignKey(ResearchBudget, on_delete=models.CASCADE, verbose_name='연구과제')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='신청자'
    )
    application_date = models.DateField(verbose_name='신청일자')
    execution_date = models.DateField(verbose_name='집행일자', null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='신청금액')
    description = models.TextField(verbose_name='신청내용')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='신청', verbose_name='상태')
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='기각사유')
    budget_subcategory = models.CharField(max_length=100, verbose_name='연구비항목')
    
    def __str__(self):
        return f"{self.application_number} - {self.research_budget.project_name}"

    class Meta:
        verbose_name = '연구비신청'
        verbose_name_plural = '연구비신청 목록'

class PaymentMethod(models.Model):
    application = models.OneToOneField(ResearchApplication, on_delete=models.CASCADE, verbose_name='신청서')
    is_card = models.BooleanField(default=False, verbose_name='카드사용여부')
    card_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='카드번호')
    bank_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='은행명')
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='계좌번호')
    
    def __str__(self):
        return f"Payment for {self.application.application_number}"

    class Meta:
        verbose_name = '지불방법'
        verbose_name_plural = '지불방법 목록'

class Attachment(models.Model):
    application = models.ForeignKey(ResearchApplication, on_delete=models.CASCADE, verbose_name='신청서')
    file_name = models.CharField(max_length=200, verbose_name='파일명')
    file = models.FileField(upload_to='attachments/', verbose_name='파일')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')
    
    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = '첨부파일'
        verbose_name_plural = '첨부파일 목록'

class UserBankAccount(models.Model):
    BANK_CHOICES = [
        ('국민', '국민'),
        ('기업', '기업'),
        ('NH농협', 'NH농협'),
        ('신한', '신한'),
        ('우체국', '우체국'),
        ('SC', 'SC'),
        ('하나', '하나'),
        ('한국씨티', '한국씨티'),
        ('우리', '우리'),
        ('산업', '산업'),
        ('새마을금고연합회', '새마을금고연합회'),
        ('케이뱅크', '케이뱅크'),
        ('카카오', '카카오'),
        ('토스', '토스'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=20, choices=BANK_CHOICES, verbose_name='은행')
    account_number = models.CharField(max_length=50, verbose_name='계좌번호')
    account_holder = models.CharField(max_length=100, verbose_name='예금주')
    is_default = models.BooleanField(default=False, verbose_name='기본계좌여부')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '사용자 계좌정보'
        verbose_name_plural = '사용자 계좌정보 목록'
        unique_together = ['user', 'bank_name', 'account_number']

    def save(self, *args, **kwargs):
        if self.is_default:
            # 다른 계좌들의 기본계좌 설정을 해제
            UserBankAccount.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class ResearchCard(models.Model):
    research = models.ForeignKey('Research', on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16, verbose_name='카드번호')
    is_active = models.BooleanField(default=True, verbose_name='사용가능여부')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '연구비카드'
        verbose_name_plural = '연구비카드 목록'
        unique_together = ['research', 'card_number']

    def clean(self):
        if len(self.card_number) < 14 or len(self.card_number) > 16:
            raise ValidationError('카드번호는 14~16자리여야 합니다.')

# PaymentMethod 모델 수정
class PaymentMethod(models.Model):
    application = models.OneToOneField('ResearchApplication', on_delete=models.CASCADE, verbose_name='신청서')
    is_card = models.BooleanField(default=False, verbose_name='카드사용여부')
    card = models.ForeignKey('ResearchCard', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='연구비카드')
    bank_account = models.ForeignKey('UserBankAccount', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='계좌정보')

    class Meta:
        verbose_name = '지불방법'
        verbose_name_plural = '지불방법 목록'

class StaffRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('approved', '승인'),
        ('rejected', '거절')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='staff_requests',
        null=True,  # 이 부분 추가
        blank=True,  # 이 부분 추가
        verbose_name='신청자'
    )
    desired_username = models.CharField(max_length=150, verbose_name='사용할 ID')  # 추가
    password = models.CharField(max_length=128, verbose_name='비밀번호')  # 추가
    reason = models.TextField(verbose_name='신청 사유')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='신청일시')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='상태'
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='검토일시'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reviewed_requests',
        verbose_name='검토자'
    )
    rejection_reason = models.TextField(
        null=True, 
        blank=True,
        verbose_name='거절 사유'
    )

    class Meta:
        verbose_name = '관리자 신청'
        verbose_name_plural = '관리자 신청 목록'
        ordering = ['-created_at']