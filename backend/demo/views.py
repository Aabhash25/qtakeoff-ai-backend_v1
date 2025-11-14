from rest_framework.views import APIView
from .serializers import BookDemoSerializer
from .models import BookDemo
from rest_framework import status
from rest_framework.response import Response
from .tasks import send_book_demo


class BookDemoAPIView(APIView):
    permission_classes = []

    def post(self, request, format=None):
        serializer = BookDemoSerializer(data=request.data)
        if serializer.is_valid():
            demo = serializer.save()
            subject = "New Demo Booking Received"
            message = f"""
                <p><strong>Name:</strong> {demo.full_name}</p>
                <p><strong>Email:</strong> {demo.email}</p>
                <p><strong>Company:</strong> {demo.company or 'N/A'}</p>
                <p><strong>Preferred Date:</strong> {demo.preferred_date}</p>
                <p><strong>Description:</strong></p>
                <p>{demo.description}</p>
            """
            send_book_demo.delay(subject, message, demo.email)

            return Response(
                {"message": "Demo booked successfully!", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)