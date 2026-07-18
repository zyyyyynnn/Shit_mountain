public class CleanDiscountCalculator {
    enum UserType {
        VIP,
        NORMAL,
        UNKNOWN
    }

    public static int calculate(int price, UserType userType, boolean festival, int couponCode) {
        int discount = membershipDiscount(price, userType, festival)
                + couponDiscount(couponCode);
        return Math.max(0, price - discount);
    }

    private static int membershipDiscount(int price, UserType userType, boolean festival) {
        return switch (userType) {
            case VIP -> price > 100 ? (festival ? 30 : 20) : 5;
            case NORMAL -> festival ? 3 : 0;
            case UNKNOWN -> 0;
        };
    }

    private static int couponDiscount(int couponCode) {
        return switch (couponCode) {
            case 1 -> 10;
            case 2 -> 20;
            case 999 -> 1; // 保留有测试覆盖的遗留规则
            default -> 0;
        };
    }

    public static void main(String[] args) {
        System.out.println(calculate(120, UserType.VIP, true, 2));
    }
}
