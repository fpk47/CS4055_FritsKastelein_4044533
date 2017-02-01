from ryu.app.flow_route import FlowRoute
import time

class Dijkstra( object ):

	def __init__( self ):
		return

	def reset( self, i_numberOfSwitches ):
		self.costs = [ 99999 for y in xrange( i_numberOfSwitches ) ]
		self.previous = [ -1 for y in xrange( i_numberOfSwitches ) ]
		self.visited = [ False for y in xrange( i_numberOfSwitches ) ]
		return

	def calculate( self, i_src_mac, i_dst_mac, i_start_index, i_end_index, i_switches, i_switches_id, i_links, i_hashmap_2  ):
		#print "Dijkstra: calculate: i_start_index = " + repr( i_start_index) + ", i_end_index = " + repr(i_end_index)

		if i_start_index == i_end_index:
			route_index = [ i_start_index ]
			return FlowRoute( i_src_mac, i_dst_mac, route_index, i_switches, i_switches_id, i_links, i_hashmap_2 )

		numberOfSwitches = len( i_links[0] )
		self.reset( numberOfSwitches )

		self.costs[ i_start_index ] = 0
		self.visited[ i_start_index ] = False

		while False in self.visited:
			index = self.getSmallestNotVisitedIndex( numberOfSwitches )
			neighbours = self.getNeighbours( numberOfSwitches, index, i_links )
			currentCost = self.costs[ index ]

			for i in range( 0, len(neighbours) ):
				newCost = currentCost + 1 # TODO add latency o.i.d.

				if newCost < self.costs[ neighbours[i] ]:
					self.costs[ neighbours[i] ] = newCost
					self.previous[ neighbours[i] ] = index

			self.visited[ index ] = True


		route_index = self.getPath( i_start_index, i_end_index )	

		flow_route = FlowRoute( i_src_mac, i_dst_mac, route_index, i_switches, i_switches_id, i_links, i_hashmap_2 )
		return flow_route
				
	def getPath( self, i_start_index, i_end_index ):
		counter = 0
		result = [ i_end_index ]
		index = i_end_index

		while index != i_start_index and counter < 10:
			result.append( self.previous[ index ] )
			index = self.previous[ index ]
			counter = counter + 1

		if counter == 10:
			while True:
				print "Dijkstra: Error: RESTART CONTROLLER"
				time.sleep(1)

		return self.reversePath(result)

	def reversePath( self, i_result ):
		result = []
		length = len(i_result)

		for i in range( 0, length ):
			result.append( i_result[ length - 1 - i ] )

		return result

	def getNeighbours( self, i_numberOfSwitches, i_start_index, i_links ):
		result = []

		for i in range( 0, i_numberOfSwitches ):
			if i_links[ i_start_index ][ i ] != -1:
				result.append( i )

		return result

	def getSmallestNotVisitedIndex( self, i_numberOfSwitches ):
		index = -1
		smallest = 999999999

		for i in range( 0, i_numberOfSwitches ):
			if self.costs[i] < smallest and self.visited[i] == False:
				index = i
				smallest = self.costs[i]

		return index







