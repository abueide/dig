public class H34 {

    public static void vtrace(int x, int y, int i, int m, int n) {}
    public static void main (String[] args) {
	mainQ(Integer.parseInt(args[0]));
    }

    public static void mainQ(int n){
	int x = 0;
	int y = 0;
	int i = 0;
	int m = 10;

	while (i < n) {
	    i++;
	    x++;
	    if (i % 2 == 0) y++;
	}
	//manual
	vtrace(x, y, i, m, n);
	//if (i == m) {
	    //assert(x == 2 * y);
	//}
	
    }
}
