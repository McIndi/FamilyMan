from .models import Family
from .models import Membership

class FamilyContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_family_role = None
        if request.user.is_authenticated:
            family_id = request.session.get('current_family_id')
            if not family_id:
                families = request.user.families.all()
                if families.count() == 1:
                    family_id = families.first().id
                    request.session['current_family_id'] = family_id

            if family_id:
                request.current_family = request.user.families.filter(id=family_id).first()
                if not request.current_family:
                    request.session.pop('current_family_id', None)
                else:
                    membership = Membership.objects.filter(
                        user=request.user,
                        family=request.current_family,
                    ).first()
                    if membership:
                        request.current_family_role = membership.role
            else:
                request.current_family = None
        else:
            request.current_family = None
        return self.get_response(request)