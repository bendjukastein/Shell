import threading
import queue
from time import sleep, time
from shell_types import *


class Shell:
	# threadCount: the maximum number of threads at one time.
	# pollFunctionsList: the list of poll functions to run through continuously
	def __init__(self, threadCount, pollFunctionsList):
		self.pq = queue.PriorityQueue()
		self.stop = True
		self.minPollTime = 0.01

		self.pfl = pollFunctionsList
		# Requires at least 3 threads to run
		# Note: number is 4 due to it returning control (which is a thread) to whatever called shell.start
		# Note: program might be more efficient with more threads (less time burned in main threads)
		if threadCount < 4:
			threadCount = 4
		self.maxThreads = threadCount

	# Start both necessary threads, then return control. Runs until a shell.stop() call
	def run(self):
		self.stop = False
		t = threading.Thread(target=self.poll_loop)
		t.start()
		t = threading.Thread(target=self.event_loop)
		t.start()

	def stop(self):
		self.stop = True

	# Loops through every polling function
	def poll_loop(self):
		# Close this thread if there aren't any poll functions stored in the list
		if len(self.pfl) == 0:
			print("No poll functions - closing thread")
			return

		# Loop through all polling functions
		# TODO: add a minimum time before repetitions
		prevTime = time()
		currTime = time()
		while not self.stop:
			prevTime = currTime
			currTime = time()
			if currTime - prevTime < self.minPollTime:
				sleep(self.minPollTime - (currTime - prevTime))
			for f in self.pfl:
				res = f()
				if res:
					# note: funct would be better off renamed "pq_obj" - it's not a function; it's a Pq_obj
					for funct in res:
						self.pq.put(funct)

	# TODO: add some way to kill a thread that takes too long
	# Handles tasks from priority queue
	def event_loop(self):
		while not self.stop:
			if threading.active_count() < self.maxThreads and self.pq.qsize() > 0:
				obj = self.pq.get()
				# print(str(threading.active_count()) + "/" + str(self.maxThreads) + " threads running")
				t = threading.Thread(target=self.funct_runner, args=[obj.func, obj.args])
				t.start()
			else:
				sleep(0.01)

	# Takes a single task from the queue, runs it, and places the returned task(s) back in the queue
	# inputs: target: a function, taking 0 or one arguments
	# args: a single argument (can be anything) or None. Not passed to function if given None
	def funct_runner(self, target, args):
		res = None
		if args:
			res = target(args)
		else:
			res = target()
		if res:
			for funct in res:
				self.pq.put(funct)


# -------------------------------------------------------------------------------------------
# Below this line is NOT part of Shell's implementation


# Simple object for testing Shell. Uses a polled timer to add a task to the queue, which then prints
class Demo_obj:
	def __init__(self, val):
		self.val = val
		self.time = time()

	# Ensures this doesn't happen more often than every val seconds
	def poll_function(self):
		if time() - self.time > self.val:
			self.time = time()
			#3 is the priority of this event
			return [Pq_obj(3, self.event_function)]

	# Checks that functions can be returned by polled functions
	def event_function(self):
		print("Event function " + str(self.val) + " is running on a thread")
		# Note: testing purposes only. NEVER put a sleep call in a real module!
		# sleep(10)
		return [Pq_obj(3, self.do_later_function, self.val + 1)]

	# checks that functions can be returned by functions in queue
	def do_later_function(self, num):
		print("This ran a bit later from event function " + str(num - 1))


# A demo for how to use.
# Note: should actually be set up and called through a separate 'start.py' file
def main():
	functions = []
	obj = Demo_obj(1.11)
	functions.append(obj.poll_function)
	obj = Demo_obj(1.414)
	functions.append(obj.poll_function)

	shell = Shell(8, functions)
	shell.run()			# Start both loops
	# sleep(6)
	# shell.stop()


if __name__ == "__main__":
	main()
