public class AuditLog {
    private int entries;

    public void record() {
        entries++;
    }

    public int count() {
        return entries;
    }
}
