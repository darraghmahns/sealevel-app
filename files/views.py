# files/views.py

import mimetypes
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from asgiref.sync import async_to_sync
from .models import File, FileAccess
from .forms import FileUploadForm
from access_log.solana_utils import log_access, retrieve_access_logs  # Adjust the import path as needed
from users.models import User


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

            # Save the file instance to get the ID
            file_instance.save()

            # Log the upload action asynchronously
            async_to_sync(log_access)(request.user, 'uploaded', file_instance)

            return redirect('file-list')
    else:
        form = FileUploadForm(user=request.user)
    return render(request, 'files/file_upload.html', {'form': form})


@login_required
def file_list_view(request):
    if request.user.is_provider:
        # Providers see all files they uploaded
        files = File.objects.filter(uploaded_by=request.user).select_related('owner', 'uploaded_by')
    else:
        # Patients see their own files and files shared with them
        owned_files = File.objects.filter(owner=request.user).select_related('owner', 'uploaded_by')
        shared_files = File.objects.filter(access_list__user=request.user).exclude(owner=request.user).select_related('owner', 'uploaded_by')
        files = owned_files | shared_files
    return render(request, 'files/file_list.html', {'files': files})


@login_required
def file_download_view(request, pk):
    file = get_object_or_404(File, pk=pk)
    
    # Check permissions
    if (file.owner == request.user or
        file.uploaded_by == request.user or
        FileAccess.objects.filter(file=file, user=request.user).exists()):

        action = "downloaded"
        # Log to Solana asynchronously
        async_to_sync(log_access)(request.user, action, file)

        # Serve the file
        file_path = file.uploaded_file.path
        file_mimetype, _ = mimetypes.guess_type(file_path)
        fs = FileSystemStorage()
        with fs.open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=file_mimetype)
            response['Content-Disposition'] = f'attachment; filename={file.uploaded_file.name}'
            return response
    else:
        return HttpResponseForbidden("You do not have permission to access this file.")


@login_required
def file_access_log_view(request, pk):
    file = get_object_or_404(File, pk=pk)
    
    # Ensure the user has access to view logs
    if not (file.owner == request.user or
            file.uploaded_by == request.user or
            FileAccess.objects.filter(file=file, user=request.user).exists()):
        return HttpResponseForbidden("You do not have permission to view access logs for this file.")

    # Retrieve access logs asynchronously
    access_logs = async_to_sync(retrieve_access_logs)(file)

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
                access_entry, created = FileAccess.objects.get_or_create(file=file, user=user_to_share)
                if created:
                    messages.success(request, f"File shared with {user_to_share.email}.")
                    action = "shared with " + user_to_share.email
                    # Log to Solana asynchronously
                    async_to_sync(log_access)(request.user, action, file)
                else:
                    messages.info(request, f"File is already shared with {user_to_share.email}.")
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
        action = "revoked access for " + access_entry.user.email
        # Log to Solana asynchronously
        async_to_sync(log_access)(request.user, action, file)
    except FileAccess.DoesNotExist:
        messages.error(request, "Access entry does not exist.")
    return redirect('file-share', pk=file.id)

@login_required
def file_delete_view(request, pk):
    file = get_object_or_404(File, pk=pk, owner=request.user)
    file.delete()
    messages.success(request, "File deleted.")
    return redirect('file-list')