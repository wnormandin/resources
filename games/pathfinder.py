#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import collections
import heapq

class Queue:
    """ Basic queue implementation using collections.deque() """

    def __init__(self):
        self.elements = collections.deque()

    def empty(self):
        """ Test if queue is empty """
        return len(self.elements)==0

    def put(self, x):
        self.elements.append(x)

    def get(self):
        return self.elements.popleft()

class PriorityQueue:
    """ Queue implementation using binary heaps """

    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements)==0

    def put(self, item, priority):
        heapq.heappush(self.elements,(priority,item))

    def get(self):
        return heapq.heappop(self.elements)[1]

class Pathfinder:

    """ Performs basic pathfinding operations """

    a_star = 0      # A* algorithm (default)
    b_first = 1     # Breadth first
    gb_first = 2    # Greedy best-first

    def __init__(self,alg=0):
        self.early_exit = True
        self.impediments = []
        self.alg = alg
        self.g = None
        self.start = None
        self.dest = None

    def execute(self):

        assert self.g is not None, 'Graph (Pathfinder.g) not initialized!'
        assert self.start is not None, 'Start point not specified!'
        assert self.dest is not None, 'End point not specified!'

        if self.alg==Pathfinder.a_star:
            results = self.a_star(self.g,self.start,self.dest)
        elif self.alg==Pathfinder.b_first:
            results = self.bf_search(self.g,self.start,self.dest)
        elif self.alg==Pathfinder.gb_first:
            results = self.gbf_search(self.g,self.start,self.dest)
        else:
            results = False

        return results

    def gbf_search(self,graph,start,goal):
        """ Greedy Best-First search """
        frontier = PriorityQueue()
        frontier.put(start,0)
        came_from = {}
        came_from[start] = None

        while not frontier.empty():
            current = frontier.get()

            if current == goal and self.early_exit:
                break

            for next in graph.neighbor(current):
                if next not in came_from:
                    priority = self.heuristic(goal,next)
                    frontier.put(next,priority)
                    came_from[next] = current

        return came_from

    def bf_search(self,graph,start,goal):
        """ Breadth-First algorithm search function """
        frontier = Queue()
        frontier.put(start)
        came_from = {}
        came_from[start]=True

        # Loop until the frontier is empty
        while not frontier.empty():
            current = frontier.get()

            # Early exit point, optional for
            # breadth-first searching (faster)
            if current == goal and self.early_exit:
                break

            for next in graph.neighbors(current):
                if next not in came_from:
                    priority = heuristic(goal,next)
                    frontier.put(next, priority)
                    came_from[next] = True

        return came_from

    def a_star(self,graph,start,goal):
        frontier = PriorityQueue()
        frontier.put(start,0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current = frontier.get()

            if current == goal and self.early_exit:
                break

            for next in graph.neighbor(current):
                new_cost = cost_so_far[current]+graph.cost(current,next)
                if next not in cost_so_far or new_cost<cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(goal,next)
                    frontier.put(next,priority)
                    came_from[next] = current

        return came_from, cost_so_far

    def heuristic(self,a,b):
        (x1,y1) = a
        (x2,y2) = b
        return abs(x1-x2) + abs(y1-y2)

class GraphGrid:

    def __init__(self,grid):

        # Detect grid size
        self.dim_y = len(grid)
        self.dim_x = len(grid[0])

        self.impassable = None

    # Tests whether the point exists
    def in_bounds(self, id):
        (x,y) = id
        return 0 <= x < self.dim_x and 0 <= y < self.dim_y

    # Checks for coordinate in list of unpassable tiles
    def passable(self, id):
        assert self.impassable is not None, 'Not assigned! grid.passable'
        return id not in self.impassable

    # Sets edges by inspecting neighboring tiles
    def neighbor(self, id):

        (x,y) = id
        results = [(x+1,y),(x,y-1),(x-1,y),(x,y+1)]

        if (x+y) % 2 == 0:
            results.reverse()

        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        return results

    # Calculates the movement cost
    def cost(self,start,end):
        return 1

