public class EverythingManagerFinalV2 {
    private int stock = 10;
    private int auditCount = 0;
    private int paymentRetries = 0;
    private String currentUser = "";
    private String currentOrder = "";
    private String lastPayment = "";
    private String lastEmail = "";
    private boolean bossMode = false;

    public String processOrder(String userId, int unitPrice, int quantity, String paymentType, boolean vip, boolean bossRequestedFreeShipping) {
        currentUser = userId;
        currentOrder = "1001";
        bossMode = bossRequestedFreeShipping;

        // 为了方便，先放这里
        if (userId == null || userId.isBlank()) {
            auditCount = auditCount + 1;
            return "INVALID_USER";
        }

        if (quantity <= 0) {
            auditCount = auditCount + 1;
            return "INVALID_QUANTITY";
        }

        if (stock < quantity) {
            auditCount = auditCount + 1;
            return "OUT_OF_STOCK";
        }

        int subtotal = unitPrice * quantity;
        int discount = 0;

        if (vip) {
            if (subtotal > 500) {
                discount = 50;
            } else {
                if (subtotal > 200) {
                    discount = 20;
                } else {
                    discount = 5;
                }
            }
        }

        int shipping = 25;
        if (subtotal > 300) {
            shipping = 0;
        }
        if (bossMode) {
            shipping = 0;
        }

        int total = subtotal - discount + shipping;
        boolean paid = false;

        // 临时补丁，先这样
        try {
            if ("CARD".equals(paymentType)) {
                if (total > 9999) {
                    lastPayment = "REVIEW";
                } else {
                    lastPayment = "PAID";
                    paid = true;
                }
            } else {
                if ("TRANSFER".equals(paymentType)) {
                    lastPayment = "PAID";
                    paid = true;
                } else {
                    lastPayment = "REJECTED";
                }
            }
        } catch (Exception ignored) {
            paymentRetries = paymentRetries + 1;
            lastPayment = "RETRY";
        }

        if (!paid) {
            auditCount = auditCount + 1;
            return "PAYMENT_" + lastPayment;
        }

        stock = stock - quantity;
        auditCount = auditCount + 1;
        lastEmail = "sent:" + currentUser + ":" + total;

        if (lastEmail.startsWith("sent:")) {
            lastEmail = "sent";
        }

        return "ORDER-" + currentOrder
                + "|PAID"
                + "|stock=" + stock
                + "|mail=" + lastEmail
                + "|audit=" + auditCount;
    }

    public static void main(String[] args) {
        EverythingManagerFinalV2 manager = new EverythingManagerFinalV2();
        System.out.println(manager.processOrder("u-42", 120, 3, "CARD", true, false));
    }
}
