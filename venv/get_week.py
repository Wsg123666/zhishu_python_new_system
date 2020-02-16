
class GetWeek:
    def __init__(self):
        self.weekCycle = [None,"", "单", "双"]
        self.result = ""
    def addAbbreviate(self,cycle,begin,end):
        if type(self.result)==str and self.result != "":
            self.result += " "
        if begin==end:
            self.result += str(begin)
        else:
            self.result+=self.weekCycle[cycle]+ str(begin) +"-" + str(end)
        return self.result

    def mashalOdd(self,result,weekOccupy,From,start):

        if (start - From +2) % 2 == 0:
            cycle = 3
        else:
            cycle = 2
        i = start + 2
        while i <len(weekOccupy) :
            if weekOccupy[i] == "1":
                if weekOccupy[i+1] == "1":
                    self.addAbbreviate(cycle,start - From + 2,i - 2 -From +2)
                    return i
            else:
                if i -2 == start:
                    cycle = 1
                self.addAbbreviate(cycle,start - From + 2,i - 2 - From +2)
                return i + 1
            i += 2
        return i
    def mashalContinue(self,result,weekOccupy,From,start):
        cycle = 1
        i = start + 2
        while i <len(weekOccupy) :
            if weekOccupy[i] == "1":
                if weekOccupy[i+1] != "1":
                    self.addAbbreviate(cycle,start - From + 2,i  -From +2)
                    return i + 2
            else:
                self.addAbbreviate(cycle,start - From + 2,i - 1 - From +2)
                return i + 1
            i += 2
        return i
    def repeatChar(self,str,length):
        if length <=1 :
            return str
        rs = ""
        k = 0
        while k<length:
            rs += str
            k+=1
        return rs
    def marshal(self,weekOccupy,From,startWeek,endWeek):
        self.result = ""
        if not weekOccupy:
            return ""

        initLength = len(weekOccupy)

        if From > 1:
            before = weekOccupy[0:From - 1]
            if before.find("1") != -1:
                weekOccupy = weekOccupy + before
        tmpOccupy = self.repeatChar("0",From+ startWeek - 2)
        tmpOccupy += weekOccupy[From+ startWeek - 2:From+ endWeek - 1]
        tmpOccupy += self.repeatChar("0", initLength - len(weekOccupy))
        weekOccupy = tmpOccupy

        if endWeek > len(weekOccupy):
            endWeek = len(weekOccupy)

        if weekOccupy.find('1') == -1:
            return ""
        weekOccupy += "000"
        start = 0
        while  weekOccupy[start] != "1":
            start +=1
        i = start + 1
        while i < len(weekOccupy):
            post = weekOccupy[start + 1]
            if post == '0':
                start = self.mashalOdd(self.result, weekOccupy, From, start)
            if post == '1':
                start = self.mashalContinue(self.result, weekOccupy, From, start)
            while start < len(weekOccupy) and weekOccupy[start] != "1":
                start+=1
            i = start
        return self.result

if __name__ == '__main__':
    b = GetWeek()
    result = b.marshal("00000000000010101000000000000000000000000000000000000",2,1,20)
    print(result)
