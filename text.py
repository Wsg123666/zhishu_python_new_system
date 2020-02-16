import execjs
p = """
var weekCycle =[];
	weekCycle[1]="";// "%u8FDE";
	weekCycle[2]="单";
    weekCycle[3]="双";
	var result = new String("");
    var weeksPerYear = 53 ;
    function addAbbreviate(cycle,begin,end){
   	    if(result!=""){
   	    	result +=" ";
   	    }
   	    if(begin==end){ // only one week
          result+= begin;
        }
        else {
          result+= unescape(weekCycle[cycle]) + begin+ "-" + end;
        }
        return result;   	    
   	}
	// 缩略单周,例如"10101010"
	function mashalOdd(result,weekOccupy,from,start) {
		var cycle = 0;
		if ((start - from + 2) % 2 == 0){
			cycle = 3;
		}
		else{
			cycle = 2;
		}
		var i = start + 2;
		for (; i < weekOccupy.length; i += 2) {
			if (weekOccupy.charAt(i) == '1') {
				if (weekOccupy.charAt(i + 1) == '1') {
					addAbbreviate(cycle, start - from + 2, i-2- from + 2);
					return i;
				}
			} else {
				if (i - 2 == start){
					cycle = 1;
				}
				addAbbreviate(cycle, start - from + 2, i - 2- from + 2);
				return i + 1;
			}
		}
		return i;
	}

	// 缩略连续周
	function mashalContinue(result,weekOccupy,from,start) {
		var cycle = 1;
		var i = start + 2;
		for (; i < weekOccupy.length; i += 2) {
			if (weekOccupy.charAt(i) == '1') {
				if (weekOccupy.charAt(i + 1) != '1') {
					addAbbreviate(cycle, start - from + 2, i- from + 2);
					return i + 2;
				}
			} else {
				addAbbreviate(cycle, start - from + 2, i - 1- from + 2);
				return i + 1;
			}
		}
		return i;
	}
	function repeatChar(str,length){
   	    if(length<=1){
   	       return str;
   	    }
   	    var rs="";
   	    for(var k=0;k<length;k++){
          rs += str;
        }
        return rs;
   	}
   	/**
	 * 对教学周占用串进行缩略表示 marsh a string contain only '0' or '1' which named
	 * "vaildWeeks" with length 53
	 * 00000000001111111111111111100101010101010101010100000 |
	 * |--------------------------------------| (from) (kstartWee) (endWeek)
	 * from is start position with minimal value 1,in login it's calendar week
	 * start startWeek is what's start position you want to mashal baseed on
	 * start,it also has minimal value 1 endWeek is what's end position you want
	 * to mashal baseed on start,it also has minimal value 1
	 */
    function marshal(weekOccupy,from,startWeek,endWeek){
        result="";
   	    if (null == weekOccupy){
   	       return "";
   	    }
   	    var initLength = weekOccupy.length;   
        if (from > 1) {
            var before = weekOccupy.substring(0, from - 1);
            if (before.indexOf('1') != -1){
                weekOccupy = weekOccupy + before;
             }
        }
        var tmpOccupy = repeatChar("0", from + startWeek - 2);
        tmpOccupy += weekOccupy.substring(from + startWeek - 2,from + endWeek - 1);
        tmpOccupy += repeatChar("0",initLength - weekOccupy.length);
        weekOccupy = tmpOccupy;
        
        if (endWeek > weekOccupy.length){
            endWeek = weekOccupy.length;
        }
        if(weekOccupy.indexOf('1') == -1){
            return "";
        }
        weekOccupy += "000";
		var start = 0;
		while ('1' != weekOccupy.charAt(start)){
			start++;
	    }
		var i = start + 1;
		while (i < weekOccupy.length) {
			var post = weekOccupy.charAt(start + 1);
			if (post == '0'){
				start = mashalOdd(result, weekOccupy,from, start);
		    }
			if (post == '1'){
				start = mashalContinue(result, weekOccupy,from, start);
		    }
			while (start < weekOccupy.length && '1' != weekOccupy.charAt(start)){
				start++;
		    }
			i = start;
		}
        return result;	
   	}

"""
js=execjs.compile(p)
result=js.call('marshal',"01111111111111111000000000000000000000000000000000000",2,1,19)
print(result)

"""
00011111111111110000000000000000000000000000000000000

00000000001111000000000000000000000000000000000000000

00000000000000110000000000000000000000000000000000000
"""

m = "111111"
print(m[0])

def get_time(occpyweek,From,startweek,endweek):
    tempweek = occpyweek