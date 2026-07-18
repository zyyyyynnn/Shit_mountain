public class OrderService {
    private static final String ORDER_ID = "1001";

    private final InventoryService inventory;
    private final PricingService pricing;
    private final PaymentService payments;
    private final NotificationService notifications;
    private final AuditLog auditLog;

    public OrderService(
            InventoryService inventory,
            PricingService pricing,
            PaymentService payments,
            NotificationService notifications,
            AuditLog auditLog) {
        this.inventory = inventory;
        this.pricing = pricing;
        this.payments = payments;
        this.notifications = notifications;
        this.auditLog = auditLog;
    }

    public OrderReceipt placeOrder(OrderRequest request) {
        validate(request);
        inventory.requireAvailable(request.quantity());

        int total = pricing.totalFor(request);
        PaymentResult payment = payments.charge(request.paymentMethod(), total);
        if (!payment.paid()) {
            auditLog.record();
            return OrderReceipt.failed("PAYMENT_" + payment.status(), auditLog.count());
        }

        inventory.reserve(request.quantity());
        String mailStatus = notifications.sendReceipt(request.userId(), total);
        auditLog.record();

        return OrderReceipt.paid(
                ORDER_ID,
                inventory.stock(),
                mailStatus,
                auditLog.count()
        );
    }

    private static void validate(OrderRequest request) {
        if (request.userId() == null || request.userId().isBlank()) {
            throw new IllegalArgumentException("userId is required");
        }
        if (request.quantity() <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
    }
}

record OrderRequest(
        String userId,
        int unitPrice,
        int quantity,
        PaymentMethod paymentMethod,
        boolean vip,
        boolean bossRequestedFreeShipping) {
}

record OrderReceipt(
        String orderId,
        String status,
        int stock,
        String mailStatus,
        int auditCount,
        String failureCode) {

    static OrderReceipt paid(
            String orderId,
            int stock,
            String mailStatus,
            int auditCount) {
        return new OrderReceipt(orderId, "PAID", stock, mailStatus, auditCount, "");
    }

    static OrderReceipt failed(String failureCode, int auditCount) {
        return new OrderReceipt("", "FAILED", -1, "not-sent", auditCount, failureCode);
    }

    String summary() {
        if (!failureCode.isEmpty()) {
            return failureCode;
        }
        return "ORDER-" + orderId
                + "|" + status
                + "|stock=" + stock
                + "|mail=" + mailStatus
                + "|audit=" + auditCount;
    }
}

enum PaymentMethod {
    CARD,
    TRANSFER
}
