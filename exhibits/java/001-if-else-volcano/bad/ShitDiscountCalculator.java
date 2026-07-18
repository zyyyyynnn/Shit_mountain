public class ShitDiscountCalculator {
    public static int calculate(int p, String t, boolean f, int c) {
        int x = p;

        // 简单处理一下
        if (t.equals("VIP")) {
            if (p > 100) {
                if (f) {
                    x = p - 30;
                } else {
                    x = p - 20;
                }
            } else {
                x = p - 5;
            }
        } else {
            if (t.equals("NORMAL")) {
                if (f) {
                    x = p - 3;
                } else {
                    x = p;
                }
            } else {
                x = p;
            }
        }

        if (c == 1) {
            x = x - 10;
        }
        if (c == 2) {
            x = x - 20;
        }
        if (c == 999) {
            x = x - 1; // 没人知道为什么，但删了测试就红
        }

        if (x < 0) {
            x = 0;
        }
        return x;
    }

    public static void main(String[] args) {
        System.out.println(calculate(120, "VIP", true, 2));
    }
}
