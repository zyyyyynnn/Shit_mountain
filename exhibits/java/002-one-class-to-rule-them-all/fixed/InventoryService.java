public class InventoryService {
    private int stock;

    public InventoryService(int openingStock) {
        this.stock = openingStock;
    }

    public void requireAvailable(int quantity) {
        if (stock < quantity) {
            throw new IllegalStateException("OUT_OF_STOCK");
        }
    }

    public void reserve(int quantity) {
        stock -= quantity;
    }

    public int stock() {
        return stock;
    }
}
