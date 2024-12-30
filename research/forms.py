from django import forms
from .models import ResearchApplication, PaymentMethod, Attachment, User, Department, Research, ResearchBudget
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import UserBankAccount, ResearchCard, PaymentMethod, StaffRequest

class ResearchApplicationForm(forms.ModelForm):
    budget_subcategory = forms.CharField(
        required=True,
        error_messages={
            'required': '연구비항목을 선택해주세요.'
        }
    )

    class Meta:
        model = ResearchApplication
        fields = [
            'research_budget',
            'application_date',
            'execution_date',
            'amount',
            'description',
            'budget_subcategory'
        ]
        error_messages = {
            'description': {
                'required': '신청내용을 입력해주세요.'
            },
            'amount': {
                'required': '신청금액을 입력해주세요.'
            },
            'application_date': {
                'required': '신청일자를 선택해주세요.'
            }
        }
        widgets = {
            'application_date': forms.DateInput(attrs={'type': 'date'}),
            'execution_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        research_budget = cleaned_data.get('research_budget')
        budget_subcategory = cleaned_data.get('budget_subcategory')
        payment_type = self.data.get('payment_type')

        if not budget_subcategory:
            raise forms.ValidationError('연구비항목을 선택해주세요.')

        # 계좌이체 선택 시 계좌 필수 체크
        if payment_type == 'bank' and not self.data.get('bank_account'):
            self.add_error('bank_account', '이 입력란을 작성하세요.')
            
        # 카드 선택 시 카드 필수 체크
        elif payment_type == 'card' and not self.data.get('card'):
            self.add_error('card', '이 입력란을 작성하세요.')
            
        # 증빙자료 필수 체크
        if not self.files.getlist('attachments') and not hasattr(self.instance, 'pk'):
            self.add_error('attachments', '이 입력란을 작성하세요.')

        if amount and research_budget:
            remaining = research_budget.calculate_remaining_amount()
            if amount > remaining:
                raise forms.ValidationError(
                    f"신청금액이 잔여예산({remaining:,}원)을 초과합니다."
                )
        return cleaned_data

class PaymentMethodForm(forms.ModelForm):
    payment_type = forms.ChoiceField(
        choices=[('card', '연구비카드'), ('bank', '계좌이체')],
        widget=forms.RadioSelect,
        initial='card'
    )

    class Meta:
        model = PaymentMethod
        fields = ['card', 'bank_account']

    def __init__(self, *args, **kwargs):
        self.research = kwargs.pop('research', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.research:
            self.fields['card'].queryset = ResearchCard.objects.filter(
                research=self.research,
                is_active=True
            )
        if self.user:
            self.fields['bank_account'].queryset = UserBankAccount.objects.filter(
                user=self.user
            )

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        
        if payment_type == 'card':
            if not cleaned_data.get('card'):
                raise forms.ValidationError('카드를 선택해주세요.')
            cleaned_data['bank_account'] = None
        else:
            if not cleaned_data.get('bank_account'):
                raise forms.ValidationError('계좌를 선택해주세요.')
            cleaned_data['card'] = None
        
        return cleaned_data

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']

class ApplicationSearchForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    project_number = forms.CharField(required=False)
    project_name = forms.CharField(required=False)
    researcher = forms.CharField(required=False)
    status = forms.ChoiceField(
        choices=[('', '전체')] + list(ResearchApplication.STATUS_CHOICES),
        required=False
    )

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '군번'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '군번을 입력하세요'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })

from django import forms
from .models import ResearchApplication, PaymentMethod, Attachment, User, Department
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

class SignUpForm(UserCreationForm):
    RANK_CHOICES = [
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
    ]

    POSITION_CHOICES = [
        ('', '선택 안함'),
        ('교수', '교수'),
        ('부교수', '부교수'),
        ('조교수(전임)', '조교수(전임)'),
        ('조교수(일반)', '조교수(일반)'),
        ('군교관', '군교관'),
        ('강사', '강사'),
        ('외래강사', '외래강사'),
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

    APPROVAL_CHOICES = [
        ('', '선택 안함'),
        ('산학협력팀장', '산학협력팀장'),
        ('과제운영팀장', '과제운영팀장'),
    ]

    username = forms.CharField(
        label='ID(군번)',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': '군번을 입력하세요'
        })
    )

    first_name = forms.CharField(
        label='이름',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': '이름을 입력하세요'
        })
    )

    internal_external = forms.ChoiceField(
        label='내/외부 구분',
        choices=[('internal', '내부'), ('external', '외부')],
        widget=forms.RadioSelect(attrs={
            'class': 'mt-1'
        })
    )

    status = forms.ChoiceField(
        label='신분 구분',
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
        })
    )

    approval_authority = forms.ChoiceField(
        label='결재권한',
        choices=APPROVAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
        })
    )

    rank = forms.ChoiceField(
        choices=RANK_CHOICES,
        label='계급',
        required=False,  # 초기에는 필수 아님
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
        })
    )

    rank_modifier = forms.ChoiceField(
        label='계급 수식어',
        choices=[('', '없음'), ('진', '(진)'), ('임', '(임)')],
        required=False,  # 초기에는 필수 아님
        widget=forms.RadioSelect(attrs={
            'class': 'mt-1'
        })
    )

    position = forms.ChoiceField(
        label='직위',
        choices=POSITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
        })
    )

    department_name = forms.CharField(  # department 필드 이름 변경
        label='소속',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': '소속을 입력하거나 검색하세요',
            'list': 'department-list',
            'autocomplete': 'off'
        })
    )

    new_department = forms.CharField(  # 새로운 소속 입력을 위한 필드
        label='새로운 소속 이름',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': '새로운 소속명을 입력하세요'
        })
    )

    email = forms.EmailField(
        label='이메일',
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'placeholder': '이메일을 입력하세요'
        })
    )

    class Meta:
        model = User
        fields = (
            'username', 'password1', 'password2', 'first_name', 
            'internal_external', 'status', 'approval_authority', 'department_name', 
            'rank', 'rank_modifier', 'position', 'email'
        )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rank = cleaned_data.get('rank')
        rank_modifier = cleaned_data.get('rank_modifier')
        department_name = cleaned_data.get('department_name')

        # 기존의 status, rank 관련 validation
        if status == '현역':
            if not rank:
                self.add_error('rank', '현역 신분은 계급을 선택해야 합니다.')
            
            if rank and rank_modifier and rank_modifier not in ['', '없음']:
                cleaned_data['rank'] = f"{rank}({rank_modifier})"
        
        elif status == '예비역':
            if not rank:
                self.add_error('rank', '예비역 신분은 계급을 선택해야 합니다.')

        # Department 처리를 cleaned_data에서 직접 department 객체로 변환
        if department_name:
            department, created = Department.objects.get_or_create(
                name=department_name,
                defaults={'code': f"DEPT_{Department.objects.count() + 1}"}
            )
            cleaned_data.pop('department_name', None)  # department_name 제거
            cleaned_data['department'] = department  # department 객체 추가

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.military_id = self.cleaned_data.get('username')
        user.internal_external = self.cleaned_data.get('internal_external')
        user.status = self.cleaned_data.get('status')
        user.position = self.cleaned_data.get('position')
        user.approval_authority = self.cleaned_data.get('approval_authority')
        
        # 계급은 현역이나 예비역일 때만 설정
        status = self.cleaned_data.get('status')
        if status in ['현역', '예비역']:
            user.rank = self.cleaned_data.get('rank')
        else:
            user.rank = None  # 명시적으로 None 설정
            
        # department 설정 (clean 메서드에서 처리된 department 객체 사용)
        if self.cleaned_data.get('department'):
            user.department = self.cleaned_data.get('department')
                
        if commit:
            user.save()
        return user
    
class ResearchForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = [
            'project_number',
            'project_name',
            'researcher',
            'researchers',
            'ordering_organization',
            'contract_from',
            'contract_to',
            'total_budget'
        ]
        widgets = {
            'contract_from': forms.DateInput(attrs={'type': 'date'}),
            'contract_to': forms.DateInput(attrs={'type': 'date'}),
            'researchers': forms.SelectMultiple(attrs={'size': '5'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        contract_from = cleaned_data.get('contract_from')
        contract_to = cleaned_data.get('contract_to')
        total_budget = cleaned_data.get('total_budget')

        if contract_from and contract_to:
            if contract_from > contract_to:
                raise forms.ValidationError('계약 종료일은 시작일보다 늦어야 합니다.')
        
        if total_budget and total_budget <= 0:
            raise forms.ValidationError('연구비 총액은 0보다 커야 합니다.')

        return cleaned_data

class ResearchBudgetForm(forms.ModelForm):
    class Meta:
        model = ResearchBudget
        fields = ['budget_type', 'total_amount']

    def clean_total_amount(self):
        total_amount = self.cleaned_data.get('total_amount')
        if total_amount and total_amount <= 0:
            raise forms.ValidationError('예산액은 0보다 커야 합니다.')
        return total_amount

class ResearchBudgetInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = sum(form.cleaned_data.get('total_amount', 0) for form in self.forms if not form.cleaned_data.get('DELETE', False))
        if hasattr(self.instance, 'total_budget') and total != self.instance.total_budget:
            raise forms.ValidationError('모든 예산 항목의 합이 연구비 총액과 일치해야 합니다.')

ResearchBudgetFormSet = forms.inlineformset_factory(
    Research,
    ResearchBudget,
    form=ResearchBudgetForm,
    formset=ResearchBudgetInlineFormSet,
    extra=1,
    can_delete=True
)

class AdminApplicationSearchForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    project_number = forms.CharField(required=False)
    project_name = forms.CharField(required=False)
    researcher = forms.CharField(required=False)
    status = forms.ChoiceField(
        choices=[('', '전체')] + list(ResearchApplication.STATUS_CHOICES),
        required=False
    )
    budget_type = forms.ChoiceField(
        choices=[('', '전체')] + list(ResearchBudget.TYPE_CHOICES),
        required=False
    )

class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = ResearchApplication
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select rounded-md shadow-sm'})
        }

class ApplicationRejectForm(forms.ModelForm):
    class Meta:
        model = ResearchApplication
        fields = ['rejection_reason']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea rounded-md shadow-sm'
            })
        }

    def clean_rejection_reason(self):
        reason = self.cleaned_data.get('rejection_reason')
        if not reason:
            raise forms.ValidationError('기각사유를 입력해주세요.')
        return reason
    
class UserBankAccountForm(forms.ModelForm):
    class Meta:
        model = UserBankAccount
        fields = ['bank_name', 'account_number', 'account_holder']
        widgets = {
            'bank_name': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'account_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '계좌번호를 입력하세요'
            }),
            'account_holder': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '예금주명을 입력하세요'
            })
        }

class ResearchCardForm(forms.ModelForm):
    class Meta:
        model = ResearchCard
        fields = ['card_number']
        widgets = {
            'card_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '카드번호를 입력하세요'
            })
        }

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        if card_number:
            # 숫자만 추출
            card_number = ''.join(filter(str.isdigit, card_number))
            if len(card_number) < 14 or len(card_number) > 16:
                raise forms.ValidationError('카드번호는 14~16자리여야 합니다.')
        return card_number

# PaymentMethod 폼 수정
class PaymentMethodForm(forms.ModelForm):
    payment_type = forms.ChoiceField(
        choices=[('card', '연구비카드'), ('bank', '계좌이체')],
        widget=forms.RadioSelect,
        initial='card'
    )
    
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'card', 'bank_account']

    def __init__(self, *args, **kwargs):
        self.research = kwargs.pop('research', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.research:
            self.fields['card'].queryset = ResearchCard.objects.filter(
                research=self.research,
                is_active=True
            )
        if self.user:
            self.fields['bank_account'].queryset = UserBankAccount.objects.filter(
                user=self.user
            )

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        
        if payment_type == 'card':
            if not cleaned_data.get('card'):
                raise forms.ValidationError('카드를 선택해주세요.')
        else:
            if not cleaned_data.get('bank_account'):
                raise forms.ValidationError('계좌를 선택해주세요.')
        
        return cleaned_data
    
class StaffRequestForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            'placeholder': '사용할 비밀번호를 입력하세요'
        }),
        help_text='영문, 숫자, 특수문자를 포함한 8자 이상의 비밀번호를 입력해주세요.'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            'placeholder': '비밀번호를 다시 입력하세요'
        })
    )

    class Meta:
        model = StaffRequest
        fields = ['desired_username', 'password', 'password_confirm', 'reason']
        widgets = {
            'desired_username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': '사용할 ID를 입력하세요'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
                'rows': 4,
                'placeholder': '신청자의 정보와 관리자 권한이 필요한 사유를 자세히 작성해주세요.'
            })
        }

    def clean_desired_username(self):
        username = self.cleaned_data.get('desired_username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('이미 사용중인 ID입니다.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if len(password) < 8:
                raise forms.ValidationError('비밀번호는 8자 이상이어야 합니다.')
            
            if not any(char.isdigit() for char in password):
                raise forms.ValidationError('비밀번호는 숫자를 포함해야 합니다.')
            
            if not any(char.isalpha() for char in password):
                raise forms.ValidationError('비밀번호는 영문자를 포함해야 합니다.')
            
            if not any(not char.isalnum() for char in password):
                raise forms.ValidationError('비밀번호는 특수문자를 포함해야 합니다.')

            if password != password_confirm:
                raise forms.ValidationError('비밀번호가 일치하지 않습니다.')

        return cleaned_data