import collections

ALLOCATED = 0
BLOCKED = 0
FREE = 1
READY = 1
MAX_PROCESSES = 16


class ProcessManager:
    def __init__(self):
        self.ProcessList = []
        self.ResourceList = []
        self.ReadyList = []

    def init(self):
        self.ProcessList = [None for x in range(16)]

        self.ResourceList = []
        self.ResourceList.append(RCB(1))
        self.ResourceList.append(RCB(1))
        self.ResourceList.append(RCB(2))
        self.ResourceList.append(RCB(3))

        self.ReadyList = []
        self.ReadyList.append([])  # priority 0, lowest
        self.ReadyList.append([])  # priority 1
        self.ReadyList.append([])  # priority 2, highest

        self.ProcessList[0] = PCB(0)
        print("\nprocess 0 created")
        self.ReadyList[0].append(0)

    def create(self, p) -> int:
        i = self.get_running()
        j = self.next_empty_index()
        if j == -1:
            return -1
        self.ProcessList[j] = PCB(p)
        self.ProcessList[j].state = READY
        self.ProcessList[i].children.append(j)
        self.ProcessList[j].parent = i
        self.ProcessList[j].children = []
        self.ProcessList[j].resources = {}
        self.ReadyList[p].append(j)
        # change readylist if new process has higher priority
        print(f"process {j} created")
        self.scheduler()
        return j

    def next_empty_index(self) -> int:
        for j in range(MAX_PROCESSES):
            if self.ProcessList[j] is None:
                return j
        return -1


    def destroy(self, j):
        n = 1
        childrenCopy = self.ProcessList[j].children.copy()
        for k in childrenCopy:
            self.destroy(k)
            n += 1
        self.ProcessList[j].children = []
        # remove j from parent's list of children
        parent = self.ProcessList[j].parent
        if parent is not None:
            self.ProcessList[parent].children.remove(j)
        if j in self.ReadyList[self.ProcessList[j].priority]:
            self.ReadyList[self.ProcessList[j].priority].remove(j)
        else:
            for resource in self.ResourceList:
                if j in resource.waitlist.keys():
                    resource.waitlist.pop(j)
        for r, k in self.ProcessList[j].resources.items():  # release all resources of j
            print(f"releasing {k} resources from resource {r}")
            self.ResourceList[r].state += k  # r.state = r.state + k
            while len(self.ResourceList[r].waitlist.items()) is not 0 and self.ResourceList[r].state > 0:
                j, k = [(x, y) for (x, y) in self.ResourceList[r].waitlist.items()][0]  # get next (j,k) from r.waitlist
                print(j, k)
                if self.ResourceList[r].state >= k:
                    self.ResourceList[r].state -= k
                    if r not in self.ProcessList[j].resources.keys():
                        self.ProcessList[j].resources[r] = k
                    else:
                        self.ProcessList[j].resources[r] += k  # insert (r,k) into j.resources
                    self.ProcessList[j].state = READY
                    del self.ResourceList[r].waitlist[j]  # remove (j,k) from r.waitlist
                    self.ReadyList[self.ProcessList[j].priority].append(j)  # insert j into RL
                else:
                    break
            self.scheduler()

        self.ProcessList[j] = None
        print(f"{n} processes destroyed")


    def request(self, r, k):
        i = self.get_running()
        if i == 0:  # process 0 cannot request resources
            return -1
        if r < 0 or r > 3:  # resource does not exist
            return -1
        if r not in self.ProcessList[i].resources.keys():  # not holding any units of r
            if k > self.ResourceList[r].inventory:
                return -1
        elif k + self.ProcessList[i].resources[r] > self.ResourceList[r].inventory:  # number of units requested + number already held >= initial inventory
            return -1

        if self.ResourceList[r].state >= k:
            self.ResourceList[r].state -= k
            if r not in self.ProcessList[i].resources.keys():
                self.ProcessList[i].resources[r] = k
            else:
                self.ProcessList[i].resources[r] += k
        else:
            self.ProcessList[i].state = BLOCKED
            self.ReadyList[self.ProcessList[i].priority].remove(i)  # remove i from RL
            self.ResourceList[r].waitlist[i] = k
            self.scheduler()

    def release(self, r, k):
        i = self.get_running()
        if r < 0 or r > 3:
            return -1
        if r not in self.ProcessList[i].resources.keys():  # process is not holding r
            return -1
        elif k > self.ProcessList[i].resources[r]:  # number of units released ≤ number of units currently held
            return -1

        if self.ProcessList[i].resources[r] == k:
            del self.ProcessList[i].resources[r] # remove (r,k) from i.resources
        else:
            self.ProcessList[i].resources[r] -= k
        self.ResourceList[r].state += k  # r.state = r.state + k
        while len(self.ResourceList[r].waitlist.items()) is not 0 and self.ResourceList[r].state > 0:
            j, k = [(x,y) for (x,y) in self.ResourceList[r].waitlist.items()][0]  # get next (j,k) from r.waitlist
            if self.ResourceList[r].state >= k:
                self.ResourceList[r].state -= k
                if r not in self.ProcessList[j].resources.keys():
                    self.ProcessList[j].resources[r] = k
                else:
                    self.ProcessList[j].resources[r] += k  # insert (r,k) into j.resources
                self.ProcessList[j].state = READY
                del self.ResourceList[r].waitlist[j]  # remove (j,k) from r.waitlist
                self.ReadyList[self.ProcessList[j].priority].append(j)  # insert j into RL
            else:
                break
        self.scheduler()

    def timeout(self) -> int:
        i = None
        if len(self.ReadyList[2]) != 0:
            i = self.ReadyList[2].pop(0)
            self.ReadyList[2].append(i)
        elif len(self.ReadyList[1]) != 0:
            i = self.ReadyList[1].pop(0)
            self.ReadyList[1].append(i)
        elif len(self.ReadyList[0]) != 0:
            i = self.ReadyList[0].pop(0)
            self.ReadyList[0].append(i)
        else:
            return -1
        self.scheduler()
        return i

    def scheduler(self) -> int:
        i = None
        if len(self.ReadyList[2]) != 0:
            i = self.ReadyList[2][0]
        elif len(self.ReadyList[1]) != 0:
            i = self.ReadyList[1][0]
        elif len(self.ReadyList[0]) != 0:
            i = self.ReadyList[0][0]
        else:
            return -1

        print(f"process {i} running")
        return i

    def get_running(self) -> int:
        if len(self.ReadyList[2]) != 0:
            return self.ReadyList[2][0]
        elif len(self.ReadyList[1]) != 0:
            return self.ReadyList[1][0]
        elif len(self.ReadyList[0]) != 0:
            return self.ReadyList[0][0]
        else:
            return -1


    def run_shell(self, input, output):
        i = open(input, "r")
        o = open(output, "w")
        lines = i.readlines()
        for line in lines:
            command = line[:2]

            # initialize
            if command == "in":
                o.write("\n")
                self.init()
                o.write(f"{self.get_running()} ")

            # create process
            elif command == "cr":
                parameters = line[3:].split(' ')
                priority = int(parameters[0])
                if priority < 0 or priority > 3:
                    o.write("-1 ")
                elif -1 == self.create(priority):
                    o.write("-1 ")
                else:
                    o.write(f"{self.get_running()} ")

            # destroy process
            elif command == "de":
                parameters = line[3:].split(' ')
                process = int(parameters[0])
                running_process = self.get_running()
                if process not in self.ProcessList[running_process].children and process != running_process:
                    o.write("-1 ")
                else:
                    self.destroy(process)
                    self.scheduler()
                    o.write(f"{self.get_running()} ")

            # request resources
            elif command == "rq":
                parameters = line[3:].split(' ')
                resource = int(parameters[0])
                num_units = int(parameters[1])
                if -1 == self.request(resource, num_units):
                    o.write("-1 ")
                else:
                    o.write(f"{self.get_running()} ")

            # release resources
            elif command == "rl":
                parameters = line[3:].split(' ')
                resource = int(parameters[0])
                num_units = int(parameters[1])
                if -1 == self.release(resource, num_units):
                    o.write("-1 ")
                else:
                    o.write(f"{self.get_running()} ")

            # timeout
            elif command == "to":
                self.timeout()
                o.write(f"{self.get_running()} ")

            elif line == "\n":
                continue

            # input exception
            else:
                o.write("-1 ")

        i.close()
        o.close()


class PCB:
    def __init__(self, priority):
        self.priority = priority
        self.state = READY
        self.parent = None
        self.children = []
        self.resources = {}  # (r:resource, k:num units holding)


class RCB:
    def __init__(self, inventory):
        self.state = inventory
        self.waitlist = collections.OrderedDict()  # (i:process index, k:num units requested)
        self.inventory = inventory


if __name__ == "__main__":
    PM = ProcessManager()
    PM.run_shell("input.txt", "output.txt")
