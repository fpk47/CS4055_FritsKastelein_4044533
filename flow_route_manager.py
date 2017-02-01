
# sh ovs-ofctl -O openflow13 dump-flows sb

from ryu.app.flow_action import FlowAction
from ryu.app.flow_route import FlowRoute

class FlowRouteManager( object ):

	def __init__( self, i_src_mac, i_dst_mac ):
		self.src_mac = i_src_mac
		self.dst_mac = i_dst_mac
		self.primary = -1
		self.secondary = -1
		return

	def get_primary_flow_route( self ):
		return self.primary

	def get_secondary_flow_route( self ):
		return self.secondary

	def clear_primary( self ):
		flow_actions = []

		if self.primary == -1:
			return flow_actions

		if self.primary != -1 and self.secondary != -1:
			port_out = [ self.secondary.get_port_out(0) ]
			flow_actions.append( FlowAction( False, True, self.secondary.get_dp(0), self.src_mac, self.dst_mac, self.secondary.get_port_in(0), port_out ) )

			length = self.primary.get_length()
			for i in range(1, length):
				flow_actions.append( FlowAction( True, False, self.primary.get_dp(i), self.src_mac, self.dst_mac, self.primary.get_port_in(i), [] ) )

		if self.primary != -1 and self.secondary == -1:
			length = self.primary.get_length()
			for i in range(0, length):
				flow_actions.append( FlowAction( True, False, self.primary.get_dp(i), self.src_mac, self.dst_mac, self.primary.get_port_in(i), [] ) )

		self.primary = -1
		return flow_actions

	def clear_secondary( self ):
		flow_actions = []

		if self.secondary == -1:
			return flow_actions

		if self.primary != -1 and self.secondary != -1:
			port_out = [ self.primary.get_port_out(0) ]
			flow_actions.append( FlowAction( False, True, self.primary.get_dp(0), self.src_mac, self.dst_mac, self.primary.get_port_in(0), port_out ) )

			length = self.secondary.get_length()
			for i in range(1, length):
				flow_actions.append( FlowAction( True, False, self.secondary.get_dp(i), self.src_mac, self.dst_mac, self.secondary.get_port_in(i), [] ) )

		if self.primary == -1 and self.secondary != -1:
			length = self.secondary.get_length()
			for i in range(0, length):
				flow_actions.append( FlowAction( True, False, self.secondary.get_dp(i), self.src_mac, self.dst_mac, self.secondary.get_port_in(i), [] ) )

		self.secondary = -1
		return flow_actions


	def get_src_mac( self ):
		return self.src_mac

	def get_dst_mac( self ):
		return self.dst_mac

	def contains_link( self, i_src_index, i_dst_index ):
		result = "NO_LINK"

		if self.primary != -1:
			if self.primary.contains_link( i_src_index, i_dst_index ):
				result = "PRIMARY"

		if self.secondary != -1:
			if self.secondary.contains_link( i_src_index, i_dst_index ):
				result = "SECONDARY"

		return result

	def install_flow_route( self, i_flow_route, i_type ):
		flow_actions = []

		if i_type == "PRIMARY":
			return self.install_flow_route_primary( i_flow_route )
		elif i_type == "SECONDARY":
			return self.install_flow_route_secondary( i_flow_route )

		return flow_actions

	def install_flow_route_primary( self, i_flow_route ):
		flow_actions = []

		src_mac = i_flow_route.get_src_mac()
		dst_mac = i_flow_route.get_dst_mac()
		length = i_flow_route.get_length()

		if self.primary == -1 and self.secondary == -1:
			for i in range(0, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )

		elif self.primary == -1 and self.secondary != -1:
			port_out = [ self.secondary.get_port_out(0) ]
			port_out.append( i_flow_route.get_port_out(0) )
			flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(0), src_mac, dst_mac, i_flow_route.get_port_in(0), port_out ) )

			for i in range(1, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )

		elif self.primary != -1 and self.secondary == -1:
			length_old = self.primary.get_length()
			for i in range(0, length_old):
				flow_actions.append( FlowAction( True, False, self.primary.get_dp(i), src_mac, dst_mac, self.primary.get_port_in(i), [] ) )

			for i in range(0, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )
		elif self.primary != -1 and self.secondary != -1:
			port_out = [ self.secondary.get_port_out(0) ]
			port_out.append( i_flow_route.get_port_out(0) )
			flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(0), src_mac, dst_mac, i_flow_route.get_port_in(0), port_out ) )

			length_old = self.primary.get_length()
			for i in range(1, length_old):
				flow_actions.append( FlowAction( True, False, self.primary.get_dp(i), src_mac, dst_mac, self.primary.get_port_in(i), [] ) )

			for i in range(1, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )
	
		self.primary = i_flow_route
		return flow_actions

	def install_flow_route_secondary( self, i_flow_route ):
		flow_actions = []

		src_mac = i_flow_route.get_src_mac()
		dst_mac = i_flow_route.get_dst_mac()
		length = i_flow_route.get_length()

		if self.primary == -1 and self.secondary == -1:
			for i in range(0, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )

		elif self.primary == -1 and self.secondary != -1:
			length_old = self.secondary.get_length()
			for i in range(0, length_old):
				flow_actions.append( FlowAction( True, False, self.secondary.get_dp(i), src_mac, dst_mac, self.secondary.get_port_in(i), [] ) )

			for i in range(0, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )

		elif self.primary != -1 and self.secondary == -1:
			port_out = [ self.primary.get_port_out(0) ]
			port_out.append( i_flow_route.get_port_out(0) )
			flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(0), src_mac, dst_mac, i_flow_route.get_port_in(0), port_out ) )

			for i in range(1, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )

		elif self.primary != -1 and self.secondary != -1:
			port_out = [ self.primary.get_port_out(0) ]
			port_out.append( i_flow_route.get_port_out(0) )
			flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(0), src_mac, dst_mac, i_flow_route.get_port_in(0), port_out ) )

			length_old = self.secondary.get_length()
			for i in range(1, length_old):
				flow_actions.append( FlowAction( True, False, self.secondary.get_dp(i), src_mac, dst_mac, self.secondary.get_port_in(i), [] ) )

			for i in range(1, length):
				port_out = [ i_flow_route.get_port_out(i) ]
				flow_actions.append( FlowAction( False, True, i_flow_route.get_dp(i), src_mac, dst_mac, i_flow_route.get_port_in(i), port_out ) )
	
		self.secondary = i_flow_route
		return flow_actions
