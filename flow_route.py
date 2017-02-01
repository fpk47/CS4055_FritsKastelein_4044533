class FlowRoute(object):

	def get_host_port( self, i_mac ):
		if i_mac in self.hashmap_2.keys():
			return self.hashmap_2[ i_mac ]
		else:
			return -1

	def contains_link( self, i_src_index, i_dst_index ):
		if len( self.index ) == 1:
			return False;
		
		for i in range( 0, len(self.index ) - 1 ):
			if self.index[i] == i_src_index and self.index[i+1] == i_dst_index:
				return True

		return False;

	def __init__( self, i_src_mac, i_dst_mac, i_route_index, i_switches, i_switches_id, i_links, i_hashmap_2 ):
		self.src_mac = i_src_mac
		self.dst_mac = i_dst_mac
		self.switches = i_switches
		self.switches_id = i_switches_id
		self.hashmap_2 = i_hashmap_2
		self.index = []
		self.dp = []
		self.dpid = []
		self.port_in = []
		self.port_out = []

		for i in range( 0, len(i_route_index) ):
			index = i_route_index[i]
			if len(i_route_index) == 1:
				self.port_in.append( self.get_host_port( i_src_mac ) )
				self.port_out.append( self.get_host_port( i_dst_mac ) )
				self.index.append( index )
				self.dp.append( i_switches[ index ] )
				self.dpid.append( i_switches_id[ index ] )
			else:
				if i == 0:
					nextIndex = i_route_index[i+1]

					self.port_in.append( self.get_host_port( i_src_mac ) )
					self.port_out.append( i_links[ index ][ nextIndex ] )
					self.index.append( index )
					self.dp.append( i_switches[ index ] )
					self.dpid.append( i_switches_id[ index ] )
				elif i == len(i_route_index) - 1:
					previousIndex = i_route_index[i-1]

					self.port_in.append( i_links[ index ][ previousIndex ] )
					self.port_out.append( self.get_host_port( i_dst_mac ) )
					self.index.append( index )
					self.dp.append( i_switches[ index ] )
					self.dpid.append( i_switches_id[ index ] )
				else:
					nextIndex = i_route_index[i+1]
					previousIndex = i_route_index[i-1]

					self.port_in.append( i_links[ index ][ previousIndex ] )
					self.port_out.append( i_links[ index ][ nextIndex ] )
					self.index.append( index )
					self.dp.append( i_switches[ index ] )
					self.dpid.append( i_switches_id[ index ] )

		if True:
			print "\n---------FlowRoute Object---------"
			print "    src: " + repr(self.src_mac)
			print "    dst: " + repr(self.dst_mac)
			print "    port_in: " + repr(self.port_in)
			print "    port_out: " + repr(self.port_out)
			print "    index: " + repr(self.index)
			print "    dpid: " + repr(self.dpid)
			print "------------------------------------\n"

		self.ready = True
		return

	def get_length( self ):
		return len(self.port_out)

	def get_src_mac( self ):
		return self.src_mac

	def get_dst_mac( self ):
		return self.dst_mac

	def get_port_in( self, i_index ):
		return self.port_in[ i_index ]

	def get_port_out( self, i_index ):
		return self.port_out[ i_index ]

	def get_index( self, i_index ):
		return self.index[ i_index ]

	def get_dp( self, i_index ):
		return self.dp[ i_index ]

	def get_dpid( self, i_index ):
		return self.dpid[ i_index ]



