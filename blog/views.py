from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse,reverse_lazy
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Q, Avg

from .models import Post,Comment,Vote
from .forms import CommentForm

def LikeView(request,pk):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked=False
    else:
        post.likes.add(request.user)
        liked=True
    return redirect(reverse('post_detail', args=[pk]))

def LikeHomeView(request,pk):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked=False
    else:
        post.likes.add(request.user)
        liked=True
    return redirect(reverse('home'))

class SummaryListView(ListView):
    model = Post
    template_name = 'summary.html'

    def get(self, request):
        x = Post.objects.order_by('-include')
        average = x.filter(include=True).aggregate(Avg('projected_yield'))
        context = { 'sorted_posts' : x, 'future_yield' : average }
        return render(request, self.template_name, context)

class BlogListView(ListView):
    model = Post
    template_name = 'home.html'


class BlogDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    def get(self, request, pk) :
        x = Post.objects.get(id=pk)
        comments = Comment.objects.filter(post=x).order_by('-updated_at')
        comment_form = CommentForm()
        stuff = get_object_or_404(Post, id=self.kwargs['pk'])
        total_likes = stuff.total_likes()
        if stuff.likes.filter(id=self.request.user.id).exists():
            liked=True
        else:
            liked=False
        context = { 'post' : x, 'comments': comments, 'comment_form': comment_form,'total_likes':total_likes,'liked':liked }
        return render(request, self.template_name, context)

class BlogCreateView(CreateView):
    model = Post
    template_name = 'post_new.html'
    fields = ['title','ticker','current_price','target_price','current_yield','projected_yield','author','body','include','rationale']

class BlogUpdateView(UpdateView):
    model = Post
    template_name = 'post_edit.html'
    fields = ['title','ticker','current_price','target_price','current_yield','projected_yield','body','include','rationale']

class BlogDeleteView(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('home')

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        f = get_object_or_404(Post, id=pk)
        comment = Comment(text=request.POST.get('comment'), author=request.user, post=f)
        comment.save()
        return redirect(reverse('post_detail', args=[pk]))

class CommentDeleteView(DeleteView):
    model = Comment
    template_name = "comment_delete.html"

    def get_success_url(self):
        post = self.object.post
        return reverse('post_detail', args=[post.id])

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError

@method_decorator(csrf_exempt, name='dispatch')
class AddVoteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Add PK",pk)
        t = get_object_or_404(Post, id=pk)
        vote = Vote(author=request.user, post=t)
        try:
            vote.save()  # In case of duplicate key
        except IntegrityError as e:
            pass
        return HttpResponse()

@method_decorator(csrf_exempt, name='dispatch')
class DeleteVoteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Delete PK",pk)
        t = get_object_or_404(Post, id=pk)
        try:
            vote = Vote.objects.get(author=request.user, post=t).delete()
        except Vote.DoesNotExist as e:
            pass
        return HttpResponse()
