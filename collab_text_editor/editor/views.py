from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, CollaboratorRole, Comment
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserRegistrationForm, AddCollaboratorForm, DocumentEditForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages

# @login_required
# def create_document(request):
#     if request.method == 'POST':
#         title = request.POST.get('title')
#         content = request.POST.get('content')
#         document = Document.objects.create(
#             title=title, 
#             content=content, 
#             owner=request.user
#         )

#         return redirect('document_detail', pk=document.pk)

#     return render(request, 'editor/create_document.html')

@login_required
def create_document(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content') 
        
        document = Document.objects.create(
            title=title, 
            content=content,  # Save the Delta JSON here
            owner=request.user
        )

        return redirect('document_detail', pk=document.pk)

    return render(request, 'editor/create_document.html')

def homepage(request):
    return render(request, 'editor/homepage.html')  

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    collaborators = CollaboratorRole.objects.filter(document=document)

    # Ensure the user has access to the document (either as owner or collaborator)
    if not (document.is_owner(request.user) or document.is_collaborator(request.user)):
        return redirect('document_list')  # Redirect if the user does not have access

    # Get the user's role on the document
    user_role = CollaboratorRole.objects.filter(document=document, user=request.user).first()
    read_only = user_role and user_role.role == 'Viewer'

    # Get a list of available users to add as collaborators (exclude the owner and existing collaborators)
    available_users = User.objects.exclude(id=document.owner.id).exclude(id__in=[collaborator.user.id for collaborator in collaborators])

    # the form for editing the document
    form = DocumentEditForm(instance=document)
    collaborator_form = AddCollaboratorForm()

    if request.method == 'POST':
        print("Really?")
        print(request.POST)
        if 'save_document' in request.POST and 'add_collaborator' not in request.POST:
            print("it got here")
            # Handle saving the document content changes
            if not read_only:
                form = DocumentEditForm(request.POST, instance=document)
                print("Form initialized with data:", request.POST) 
                print("Not read only")
                if form.is_valid():
                    print("Form is valid, saving document...")
                    document.content = request.POST.get('content') 
                    # form.save()
                    document.save()
                    return redirect('document_detail', pk=document.pk)
                else:
                    print("invalid Form")
                    print(form.errors) 

        elif 'add_collaborator' in request.POST:
            print("Collaborator got here")
            # Handle adding a collaborator
            collaborator_form = AddCollaboratorForm(request.POST)
            if collaborator_form.is_valid():
                user = collaborator_form.cleaned_data['user']
                role = collaborator_form.cleaned_data['role']
                CollaboratorRole.objects.create(document=document, user=user, role=role)
                return redirect('document_detail', pk=document.pk)

        elif 'remove_collaborator' in request.POST:
            # Handle removing a collaborator (Only the owner can remove collaborators)
            if document.is_owner(request.user):
                user_id = request.POST.get('user_id')
                collaborator = CollaboratorRole.objects.filter(document=document, user_id=user_id).first()
                if collaborator:
                    collaborator.delete()
                return redirect('document_detail', pk=document.pk)

        elif 'change_role' in request.POST:
            # Handle changing a collaborator's role (Only the owner can change roles)
            if document.is_owner(request.user):
                user_id = request.POST.get('user_id')
                new_role = request.POST.get('new_role')
                collaborator = CollaboratorRole.objects.filter(document=document, user_id=user_id).first()
                if collaborator:
                    collaborator.role = new_role
                    collaborator.save()
                return redirect('document_detail', pk=document.pk)

    collaborators = CollaboratorRole.objects.filter(document=document)

    return render(request, 'editor/document_detail.html', {
        'document': document,
        'form': form,
        'collaborator_form': collaborator_form,
        'collaborators': collaborators,
        'user_role': user_role,
        'read_only': read_only,
        'current_user': request.user, 
        'available_users': available_users
    })




def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to the login page after successful registration
    else:
        form = UserRegistrationForm()
    return render(request, 'editor/register.html', {'form': form})


def document_list(request):
    # Get all documents created by the current user or shared with them as a collaborator
    documents = Document.objects.filter(owner=request.user) | Document.objects.filter(collaborators=request.user)
    
    return render(request, 'editor/document_list.html', {'documents': documents})

@login_required
@csrf_exempt
def save_comment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        document_id = data['document_id']
        selected_text = data['selected_text']
        comment_text = data['comment_text']
        elected_range = data.get('selected_range')
        

        document = Document.objects.get(id=document_id)


        comment = Comment.objects.create(
            user=request.user,
            document=document,
            text=comment_text,
            highlighted_text=selected_text
        )

        
        return JsonResponse({'status': 'success', 'comment_id': comment.id})

    return JsonResponse({'status': 'fail'}, status=400)

@login_required
@csrf_exempt  
def autosave_document(request, doc_id):
    if request.method == "POST":
        
        document = get_object_or_404(Document, id=doc_id)
        
        
        if not (document.is_owner(request.user) or document.has_edit_permission(request.user)):
            return JsonResponse({"status": "error", "message": "Unauthorized access."}, status=403)
        
        try:
            data = json.loads(request.body)
            new_content = data.get("content", "")
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data."}, status=400)
        
        
        document.content = new_content
        document.save()
        
        return JsonResponse({"status": "success", "message": "Document autosaved successfully."})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)