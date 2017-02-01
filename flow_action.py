class FlowAction( object ):
	def __init__( self, i_deleteMode, i_addMode, i_dp, i_src_mac, i_dst_mac, i_port_in, i_port_out ):
		self.deleteMode = i_deleteMode
		self.addMode = i_addMode

		self.dp = i_dp
		self.src_mac = i_src_mac
		self.dst_mac = i_dst_mac
		self.port_in = i_port_in
		self.port_out = i_port_out
		return

	def isDeleteMode( self ):
		return self.deleteMode

	def isAddMode( self ):
		return self.addMode

	def get_dp( self ):
		return self.dp

	def get_src_mac( self ):
		return self.src_mac

	def get_dst_mac( self ):
		return self.dst_mac

	def get_port_in( self ):
		return self.port_in

	def get_port_out( self ):
		return self.port_out