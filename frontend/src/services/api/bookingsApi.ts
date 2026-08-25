import { apiRequest } from './client';

export type Booking = {
  id: string;
  customerName: string;
  businessName: string;
  meetingDate: string;
  meetingTime: string;
  location: string;
  status: string;
  externalBookingId: string | null;
  createdAt: string;
  updatedAt: string;
};

export function getConfirmedBookings() {
  return apiRequest<{ bookings: Booking[]; total: number }>('/bookings?status=CONFIRMED');
}
