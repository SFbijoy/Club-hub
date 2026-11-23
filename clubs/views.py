from django.shortcuts import HttpResponse, render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from clubs.models import Club, ClubRole, ClubMembership
from events.models import Event
from clubs.forms import ClubForm, ClubRoleForm
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator

def is_club_admin(user, club):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return club.memberships.filter(user=user, role__role_name="President", confirmed=True).exists()

def club_list(request):
    clubs = Club.objects.all()
    return render(request, 'club_list.html', {'clubs': clubs})

def club_detail(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    is_member = False
    is_pending = False
    membership_id = None 
    if request.user.is_authenticated:
        membership = ClubMembership.objects.filter(user=request.user, club=club).first()
        if membership:
            membership_id = membership.id 
            if membership.confirmed:
                is_member = True
            else:
                is_pending = True
    members = ClubMembership.objects.filter(club=club, confirmed=True)
    roles = ClubRole.objects.filter(club=club)
    events = Event.objects.filter(club=club).order_by('-date')
    committee = members.filter(role__isnull=False).select_related('user', 'role')

    return render(request, 'club_detail.html', {
        'club': club,
        'members': members,
        'roles': roles,
        'is_member': is_member,
        'is_pending': is_pending,
        'events': events,
        'committee': committee,
        'membership_id': membership_id
    })

@login_required(login_url='sign-in')
def create_club(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Only staff members can create a club.")
        return redirect('club-list')

    if request.method == 'POST':
        club_form = ClubForm(request.POST, request.FILES)
        if club_form.is_valid():
            club = club_form.save()
            president_role, _ = ClubRole.objects.get_or_create(club=club, role_name="President")
            ClubRole.objects.get_or_create(club=club, role_name="Member")
            ClubMembership.objects.create(user=request.user, club=club, role=president_role, confirmed=True)
            messages.success(request, 'Club created successfully!')
            return redirect('club-detail', club_id=club.id)
    else:
        club_form = ClubForm()
    return render(request, 'create_club.html', {'club_form': club_form})

@login_required(login_url='sign-in')
def join_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    membership, created = ClubMembership.objects.get_or_create(
        user=request.user,
        club=club,
        defaults={'confirmed': False}
    )

    if not created:
        if membership.confirmed:
            messages.info(request, "You are already a confirmed member of this club.")
        else:
            messages.info(request, "You already requested to join. Awaiting approval.")
        return redirect('club-detail', club_id=club.id)

    messages.success(request, "Your request to join the club has been submitted.")
    return redirect('club-detail', club_id=club.id)

def confirm_membership(request, membership_id, token):
    membership = get_object_or_404(ClubMembership, id=membership_id)
    if default_token_generator.check_token(membership.user, token):
        membership.confirmed = True
        membership.save()
        messages.success(request, f"Your membership for {membership.club.name} has been confirmed!")
    else:
        messages.error(request, "Confirmation link is invalid or has expired.")
    return redirect('club-detail', club_id=membership.club.id)

@login_required(login_url='sign-in')
def pending_requests(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to view pending requests.")
        return redirect('club-detail', club_id=club.id)

    pending = ClubMembership.objects.filter(club=club, confirmed=False)
    return render(request, 'pending_request.html', {
        'club': club,
        'pending': pending
    })

@login_required(login_url='sign-in')
def approve_member(request, membership_id):
    membership = get_object_or_404(ClubMembership, id=membership_id)
    club = membership.club
    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to approve members.")
        return redirect('club-detail', club_id=club.id)

    membership.confirmed = True
    membership.save()
    messages.success(request, f"{membership.user.username} has been approved!")
    return redirect('pending-requests', club_id=club.id)

@login_required(login_url='sign-in')
def reject_member(request, membership_id):
    membership = get_object_or_404(ClubMembership, id=membership_id)
    club = membership.club
    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to reject members.")
        return redirect('club-detail', club_id=club.id)

    membership.delete()
    messages.warning(request, "Membership request rejected.")
    return redirect('pending-requests', club_id=club.id)

@login_required(login_url='sign-in')
def cancel_request(request, membership_id):
    membership = get_object_or_404(ClubMembership, id=membership_id)

    if request.user != membership.user:
        messages.error(request, "You are not authorized to cancel this request.")
        return redirect('club-detail', club_id=membership.club.id)

    club_id = membership.club.id
    membership.delete()

    messages.success(request, "Your join request has been canceled.")
    return redirect('club-detail', club_id=club_id)

@login_required(login_url='sign-in')
def update_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to update this club.")
        return redirect('club-detail', club_id=club.id)

    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, f"{club.name} updated successfully!")
            return redirect('club-detail', club_id=club.id)
    else:
        form = ClubForm(instance=club)

    return render(request, 'update_club.html', {'club_form': form, 'club': club})

@login_required(login_url='sign-in')
def delete_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    # Permission rules:
    # Superuser or staff only
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this club.")
        return redirect('club-detail', club_id=club.id)

    if request.method == "POST":
        club.delete()
        messages.success(request, "Club deleted successfully!")
        return redirect('club-list')

    return render(request, "delete_club_confirm.html", {"club": club})

@login_required(login_url='sign-in')
def assign_role(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to assign roles.")
        return redirect('club-detail', club_id=club.id)

    members = ClubMembership.objects.filter(club=club, confirmed=True)
    roles = ClubRole.objects.filter(club=club)

    if request.method == 'POST':
        member_id = request.POST.get('member')
        role_id = request.POST.get('role')

        member = get_object_or_404(ClubMembership, id=member_id, club=club)
        role = get_object_or_404(ClubRole, id=role_id, club=club)

        member.role = role
        member.save()
        messages.success(request, f"{member.user.username} has been assigned as {role.role_name}.")
        return redirect('club-detail', club_id=club.id)

    return render(request, 'assign_role.html', {
        'club': club,
        'members': members,
        'roles': roles
    })

@login_required(login_url='sign-in')
def add_role(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    if not is_club_admin(request.user, club):
        messages.error(request, "You are not authorized to add roles.")
        return redirect('club-detail', club_id=club.id)

    if request.method == 'POST':
        form = ClubRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.club = club
            role.save()
            messages.success(request, f"Role '{role.role_name}' added successfully!")
            return redirect('assign-role', club_id=club.id)
    else:
        form = ClubRoleForm()

    return render(request, 'add_role.html', {'form': form, 'club': club})

@login_required(login_url='sign-in')
def member_list(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    members = ClubMembership.objects.filter(club=club, confirmed=True)

    return render(request, "member_list.html", {
        "club": club,
        "members": members,
    })

