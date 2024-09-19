import mimetypes
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import File, FileAccess
from .forms import FileUploadForm
from access_log.models import AccessLog
from access_log.solana_utils import log_access

User = get_user_model()


@login_required
def file_upload_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            file_instance = form.save(commit=False)
            if request.user.is_provider:
                # Providers upload files on behalf of patients
                owner_email = form.cleaned_data.get('owner_email')
                try:
                    owner = User.objects.get(email=owner_email)
                    file_instance.owner = owner
                    file_instance.uploaded_by = request.user
                except User.DoesNotExist:
                    form.add_error('owner_email', 'Patient with this email does not exist.')
                    return render(request, 'files/file_upload.html', {'form': form})
            else:
                # Patients upload their own files
                file_instance.owner = request.user
                file_instance.uploaded_by = request.user
            file_instance.save()
            return redirect('file-list')
    else:
        form = FileUploadForm(user=request.user)
    return render(request, 'files/file_upload.html', {'form': form})


@login_required
def file_list_view(request):
    if request.user.is_provider:
        # Providers see files they've uploaded
        files = File.objects.filter(uploaded_by=request.user)
    else:
        # Patients see their own files and files shared with them
        owned_files = File.objects.filter(owner=request.user)
        shared_files = File.objects.filter(access_list__user=request.user).exclude(owner=request.user)
        files = owned_files | shared_files
    return render(request, 'files/file_list.html', {'files': files})


@login_required
def file_download_view(request, pk):
    try:
        file = File.objects.get(pk=pk, owner=request.user)
    except File.DoesNotExist:
        raise Http404("File does not exist")
    
    if (file.owner == request.user or
        file.uploaded_by == request.user or
        FileAccess.objects.filter(file=file, user=request.user).exists()):

        action = "download"
        # Log to the database
        AccessLog.objects.create(user=request.user, file=file, action=action)
        # Log to Solana
        log_access(str(request.user.id), str(file.id), action)

        # Serve the file
        file_path = file.file.path
        file_name = file.file.name.split('/')[-1]
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    else:
        return HttpResponseForbidden("You do not have permission to access this file.")
    

@login_required
def file_access_log_view(request, pk):
    file = get_object_or_404(File, pk=pk, owner=request.user)
    access_logs = AccessLog.objects.filter(file=file).order_by('-timestamp')
    return render(request, 'files/file_access_log.html', {'file': file, 'access_logs': access_logs})


@login_required
def share_file_view(request, pk):
    file = get_object_or_404(File, pk=pk, owner=request.user)
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user_to_share = User.objects.get(email=email)
            if user_to_share == request.user:
                messages.error(request, "You cannot share the file with yourself.")
            else:
                FileAccess.objects.get_or_create(file=file, user=user_to_share)
                messages.success(request, f"File shared with {user_to_share.email}.")
                action = "share"
                # Log to the database
                AccessLog.objects.create(user=request.user, file=file, action=action)
                # Log to Solana
                log_access(str(request.user.id), str(file.id), action)
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
        return redirect('file-share', pk=file.id)
    else:
        return render(request, 'files/file_share.html', {'file': file})
    

@login_required
def revoke_access_view(request, file_id, user_id):
    file = get_object_or_404(File, pk=file_id, owner=request.user)
    try:
        access_entry = FileAccess.objects.get(file=file, user__id=user_id)
        access_entry.delete()
        messages.success(request, "Access revoked.")
        action = "revoke"
        # Log to the database
        AccessLog.objects.create(user=request.user, file=file, action=action)
        # Log to Solana
        log_access(str(request.user.id), str(file.id), action)
    except FileAccess.DoesNotExist:
        messages.error(request, "Access entry does not exist.")
    return redirect('file-share', pk=file.id)