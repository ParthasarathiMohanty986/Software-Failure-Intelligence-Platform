from django.urls import path

from .views import KnowledgeDocumentDeleteView, KnowledgeDocumentDetailView, KnowledgeDocumentListView, KnowledgeDocumentUploadView, KnowledgeSearchView

urlpatterns = [
    path("documents/", KnowledgeDocumentUploadView.as_view(), name="documents-upload"),
    path("documents/list/", KnowledgeDocumentListView.as_view(), name="documents-list"),
    path("documents/<int:pk>/", KnowledgeDocumentDetailView.as_view(), name="documents-detail"),
    path("documents/<int:pk>/delete/", KnowledgeDocumentDeleteView.as_view(), name="documents-delete"),
    path("search/", KnowledgeSearchView.as_view(), name="knowledge-search"),
]
