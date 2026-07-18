public class NotificationService {
    public String sendReceipt(String userId, int total) {
        String message = "sent:" + userId + ":" + total;
        return message.startsWith("sent:") ? "sent" : "not-sent";
    }
}
