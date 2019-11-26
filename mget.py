import requests, os, time, math, glob, argparse
from threading import Thread
from urllib.parse import urlparse

class Globals:
    def __init__(self):
        self.contained = {}
    
    def put(self,name,value):
        self.contained[name] = value

    def get(self,name):
        return self.contained[name]

    def has(self,name):
        return name in self.contained

def dlSpeed(inpt):
    if inpt == 0:
        return "0b"
    size_name = ("b", "kb", "mb", "gb")
    i = int(math.floor(math.log(inpt, 1024)))
    p = math.pow(1024, i)
    s = round(inpt / p, 2)
    return "%s %s" % (s, size_name[i])

def download(url, gbl, path = os.getcwd(), name = None, threads = 0, chunk_size = 2048):
    head = requests.head(url).headers
    length = 0
    if "Content-Length" in head:
        length = int(head["Content-Length"])
        gbl.put("length",length)
        if threads == 0:
            threads = os.cpu_count()
    else:
        threads = 1
    if name == None:
        name = os.path.basename(urlparse(url).path)
    print("Downloading "+(str(dlSpeed(length)) if length > 0 else "Unknown size"))
    print("URL: "+url)
    print("Threads: "+str(threads))
    gbl.put("threads",threads)
    gbl.put("threadData",[0 for _ in range(threads)])
    resp = requests.get(url,stream = True)
    if resp.status_code == 200:
        if threads > 1 and length > 0:
            splits = []
            for _ in range(threads-1):
                splits.append(math.floor(length/threads))
            splits.append(length - sum(splits))
            bytesplits = []
            last = 0
            for i in splits:
                bytesplits.append([last,last+i])
                last += i+1
            if last-threads != length:
                print(last,length)
                return
            else:
                gbl.put("bytesplits",bytesplits)
                thr = []
                startTime = time.time()
                for i in range(threads):
                    t = Thread(target=dlThread,args=[url,path,name,chunk_size,i,bytesplits[i],gbl])
                    thr.append(t)
                    t.start()
                while 1:
                    dead = 0
                    for i in thr:
                        if not i.is_alive():
                            dead +=1
                    if dead == len(thr):
                        break
                    time.sleep(0.5)
                m, s = divmod(time.time() - startTime, 60)
                h, m = divmod(m, 60)
                m = int(m)
                s = int(s)
                h = int(h)
                print(f'Downloaded in {h:d}:{m:02d}:{s:02d}') 
                print("Combining files..")
                files = glob.glob("*.mget_*")
                files.sort()
                with open(path+"/"+name,"wb") as f:
                    f.write(b"")
                for i in files:
                    with open(path+"/"+name,"ab") as f:
                        with open(i,"rb") as x:
                            f.write(x.read())
                    os.remove(i)
                print("Completed")    
            
def dlThread(url,path,name,chunk_size,indx,splits,gbl):
    resp = requests.get(url,stream = True,headers={"Range":"bytes=%d-%d"%(splits[0],splits[1])})
    with open(path+"/"+name+".mget_"+str(indx), 'wb') as f:
        cur = 0
        for chunk in resp.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            cur += chunk_size
            thrdata = gbl.get("threadData")
            thrdata[indx] = cur
            gbl.put("threadData",thrdata)
            upd(gbl)

def upd(gbl):
    if not gbl.has("lastSize"):
        gbl.put("lastSize",sum([x for x in gbl.get("threadData")]))
        speed = "?"
    if not gbl.has("lastTime"):
        gbl.put("lastTime",time.time())
        speed = "?"
    if not gbl.has("lastSpeed"):
        gbl.put("lastSpeed","?")
        speed = "?"
    if gbl.has("lastTime") and gbl.has("lastSize") and time.time() - gbl.get("lastTime") >= 1:
        speed = dlSpeed(sum([x for x in gbl.get("threadData")]) - gbl.get("lastSize"))
        gbl.put("lastSpeed",speed)
        gbl.put("lastTime",time.time())
        gbl.put("lastSize",sum([x for x in gbl.get("threadData")]))
    else:
        speed = gbl.get("lastSpeed")
    print(str(int((sum([x for x in gbl.get("threadData")])/int(gbl.get("length")))*100))+"% @ "+speed+"/s                       ",end="\r")

if __name__ == "__main__":
    gbl = Globals()
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-t","--threads",type=int,default=os.cpu_count(),help="Number of threads to spawn to help download.")
    parser.add_argument("-p","--path",default=os.getcwd(),help="Path to download to (If you want to set an output file name, use --output)")
    parser.add_argument("-o","--output",help="Output filename")
    parser.add_argument("-c","--chunk",default=2048,type=int,help="Chunk size to read in bytes. If set too high, it can cause some read lag and slow down the download")
    args = parser.parse_args()
    download(args.url,gbl,args.path,args.output,args.threads,args.chunk)
