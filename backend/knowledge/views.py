import os
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KnowledgeDocument
from .services import index_document, search_user_runbooks


class KnowledgeDocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        content = request.data.get("content")
        title = request.data.get("title") or (file_obj.name if file_obj else "runbook")
        if not (file_obj or content):
            return Response({"detail": "No document content provided"}, status=status.HTTP_400_BAD_REQUEST)

        if file_obj:
            file_bytes = file_obj.read()
            if not file_bytes:
                return Response({"detail": "Empty document"}, status=status.HTTP_400_BAD_REQUEST)
            content = file_bytes.decode("utf-8", errors="ignore")

        document = KnowledgeDocument.objects.create(user=request.user, title=title, content=content, file_type="markdown")
        try:
            index_document(document, content)
            return Response({"id": document.id, "title": document.title, "status": document.status})
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message"])
            return Response({"detail": "Document indexing failed", "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class KnowledgeDocumentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        docs = KnowledgeDocument.objects.filter(user=request.user)
        return Response({"results": [{
            "id": item.id,
            "title": item.title,
            "status": item.status,
            "file_type": item.file_type,
            "created_at": item.created_at.isoformat(),
        } for item in docs]})


class KnowledgeDocumentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        doc = KnowledgeDocument.objects.filter(user=request.user, id=pk).first()
        if not doc:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": doc.id, "title": doc.title, "content": doc.content[:2000], "status": doc.status})


class KnowledgeDocumentDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        doc = KnowledgeDocument.objects.filter(user=request.user, id=pk).first()
        if not doc:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        doc.delete()
        return Response({"deleted": True})


class KnowledgeSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"detail": "A query is required"}, status=status.HTTP_400_BAD_REQUEST)
        results = search_user_runbooks(request.user, query)
        return Response({"results": results})
