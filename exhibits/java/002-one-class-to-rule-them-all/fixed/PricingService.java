public class PricingService {
    private static final int VIP_LARGE_ORDER_THRESHOLD = 500;
    private static final int VIP_MEDIUM_ORDER_THRESHOLD = 200;
    private static final int FREE_SHIPPING_THRESHOLD = 300;
    private static final int LARGE_VIP_DISCOUNT = 50;
    private static final int MEDIUM_VIP_DISCOUNT = 20;
    private static final int SMALL_VIP_DISCOUNT = 5;
    private static final int STANDARD_SHIPPING = 25;

    public int totalFor(OrderRequest request) {
        int subtotal = request.unitPrice() * request.quantity();
        int discount = vipDiscount(subtotal, request.vip());
        int shipping = shippingCost(
                subtotal,
                request.bossRequestedFreeShipping()
        );
        return subtotal - discount + shipping;
    }

    private int vipDiscount(int subtotal, boolean vip) {
        if (!vip) {
            return 0;
        }
        if (subtotal > VIP_LARGE_ORDER_THRESHOLD) {
            return LARGE_VIP_DISCOUNT;
        }
        if (subtotal > VIP_MEDIUM_ORDER_THRESHOLD) {
            return MEDIUM_VIP_DISCOUNT;
        }
        return SMALL_VIP_DISCOUNT;
    }

    private int shippingCost(int subtotal, boolean freeShippingOverride) {
        if (freeShippingOverride || subtotal > FREE_SHIPPING_THRESHOLD) {
            return 0;
        }
        return STANDARD_SHIPPING;
    }
}
