public class PaymentService {
    private static final int CARD_REVIEW_THRESHOLD = 9999;

    public PaymentResult charge(PaymentMethod method, int total) {
        if (method == PaymentMethod.CARD && total > CARD_REVIEW_THRESHOLD) {
            return new PaymentResult(false, "REVIEW");
        }
        if (method == PaymentMethod.CARD || method == PaymentMethod.TRANSFER) {
            return new PaymentResult(true, "PAID");
        }
        return new PaymentResult(false, "REJECTED");
    }
}

record PaymentResult(boolean paid, String status) {
}
