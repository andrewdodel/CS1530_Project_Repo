
public class HighscoreParser {
	String bigString;
	String userID;
	int score;
	
	public static void main(String args[]) {
		String hs = "50,AndrewDodel 40,SundarSampath 30,YuxinZhang 20,BrendanCampbell";
		String newUser = "AndrewJia";
		int newScore = 10;
		hs = updateHighscores(hs, newUser, newScore);
		
		newScore = 45;
		hs = updateHighscores(hs, newUser, newScore);
		
		hs = updateHighscores(hs, "SohelSarwar", 33);
	}
	public static String updateHighscores(String bigString, String userID, int score) {
		//split by spaces
		String user = userID;
		int min = score;
		String[] temp = bigString.split(" ");
		//create 2D array that will contain string arrays containing scores and users
		String[][] scores = new String[temp.length][2];
		//populate 2D array
		for(int i = 0; i < temp.length; i ++) {
			scores[i] = temp[i].split(",");
		}
		//run through 2D array, finding lowest score.
		//order doesn't matter, many comparisons, many replacements
		for(int j = 0; j < temp.length; j ++) {
			//System.out.println(j);
			int tempScore = Integer.parseInt(scores[j][0]);
			//System.out.println(tempScore);
			if(min > tempScore) {
				String[] tempArr = scores[j].clone();
				//cloning is stupid
//				for(int x = 0; x < tempArr.length; x ++) {
//					System.out.print(tempArr[x]);
//				}
				
				scores[j][1] = user;
				scores[j][0] = Integer.toString(min);
				user = tempArr[1];
				//System.out.println(user);
				min = Integer.parseInt(tempArr[0]);
				//System.out.println(min);
			}
		}
		
		//rebuild bigString
		StringBuilder b = new StringBuilder();
		for(int k = 0; k < scores.length; k ++) {
			b.append(scores[k][0] + "," + scores[k][1] + " ");
		}
		
		System.out.println(b);
		return b.toString();
	}
}
