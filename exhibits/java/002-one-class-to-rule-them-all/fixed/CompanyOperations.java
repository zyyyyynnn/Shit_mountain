public class CompanyOperations {
    public static void main(String[] args) {
        OrderService orders = new OrderService(
                new InventoryService(10),
                new PricingService(),
                new PaymentService(),
                new NotificationService(),
                new AuditLog()
        );

        OrderRequest request = new OrderRequest(
                "u-42",
                120,
                3,
                PaymentMethod.CARD,
                true,
                false
        );

        System.out.println(orders.placeOrder(request).summary());
    }
}
