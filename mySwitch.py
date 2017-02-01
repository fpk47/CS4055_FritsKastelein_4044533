from ryu.base import app_manager
import sys
import time
import copy
from ryu.app.dijkstra import Dijkstra
from ryu.app.flow_route import FlowRoute
from ryu.app.flow_route_manager import FlowRouteManager
from ryu.app.flow_action import FlowAction
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub
from operator import attrgetter

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def _monitor(self):
        if self.mode == "MODE_0":
            mode_string = "MODE_0 | SPC"
        else: 
            mode_string = "MODE_0 | MPC"

        print "\n--------STARTING CONTROLLER---------"
        print "   mode = " + repr(mode_string)
        print "   Resetting switches (wait 5 seconds..)"
        while time.time() - self.bugTimer[1] < 5:
            hub.sleep(0.1)

        if self.bugTimer[0] == 0:
            while True:
                print "      Error: Restart controller (or no mininet available)"
                time.sleep(0.5)
        print "      Done!"
        print "   Starting createLinkMatrix, numberOfSwitches = " + repr( self.bugTimer[0] )

        for i in range( 0, self.bugTimer[0] ):
            self.createLinkMatrix( get_switch( self, None ), get_link( self, None ) )

        print "-----------------------------------\n"


        return
        while True:
            hub.sleep(2)
            for dp in self.switches:
                self._request_stats(dp)
                
    def deleteAllFlows( self, i_dp ):
        datapath = i_dp
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch()
        priority = ofproto.OFP_DEFAULT_PRIORITY
        command = ofproto.OFPFC_DELETE

        mod = parser.OFPFlowMod( datapath=datapath, match=match, command=command, priority=priority, instructions=[], 
                                 out_port = ofproto.OFPP_ANY, out_group = ofproto.OFPG_ANY )
        datapath.send_msg(mod) 
        return

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.

        datapath = ev.msg.datapath

        self.deleteAllFlows( datapath )

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        actions = [ parser.OFPActionOutput( ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER ) ] 
        inst = [ parser.OFPInstructionActions( ofproto.OFPIT_APPLY_ACTIONS, actions ) ]
        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=parser.OFPMatch(), instructions=inst)

        datapath.send_msg(mod)
        self.bugTimer[0] = self.bugTimer[0] + 1
        self.bugTimer[1] = time.time()
        return

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mode = "MODE_1" # CHOOSE FROM "MODE_0" or "MODE_1"
        self.bugTimer = [ 0, time.time() ]
        self.monitor_thread = hub.spawn(self._monitor)
        self.mac_to_port = {}
        self.switches = []
        self.printAll = False
        self.switches_id = []
        self.numberOfSwitches = 0
        self.flows = []
        self.hashmap_1 = {} # set_dst_dpid, get_dst_dpid
        self.hashmap_2 = {} # set_host_port, get_host_port
        self.hashmap_3 = {} # set_host_dpid, get_host_dpid
        self.hashmap_4 = {} # exists_mac_dpid
        self.hashmap_5 = {} # set_flow_route_manager_key, set_flow_route_manager_mac, get_route_manager_data, get_flow_route_manager_all
        self.connectedData = []
        self.dijkstra = Dijkstra()
        self.initCounter = 0

    def set_flow_route_manager_key( self, i_key, i_flow_data ):
        self.hashmap_5[ str(i_key) ] = i_flow_data
        return

    def set_flow_route_manager_mac( self, i_src_mac, i_dst_mac, i_flow_data ):
        self.hashmap_5[ str(i_src_mac) + str(i_dst_mac) ] = i_flow_data
        return

    def get_flow_route_manager_mac( self, i_src_mac, i_dst_mac ):
        key = str( i_src_mac ) + str( i_dst_mac )

        if key in self.hashmap_5.keys():
            return self.hashmap_5[ key ]
        else:
            return -1

    def get_flow_route_manager_all( self ):
        return self.hashmap_5.values()

    def deleteFlowData( self, i_src_mac, i_dst_mac ):
        if self.get_flow_data( i_src_mac, i_dst_mac ) != -1:
            self.hashmap_5[ str(i_src_mac) + str(i_dst_mac) ] = -1
        return

    def exists_src_dst_mac_dpid( self, i_mac, i_dpid):
        key = str( i_mac ) + str( i_dpid )

        if key in self.hashmap_4.keys():
            return True
        else:
            self.hashmap_4[key] = 1
            return False

    # remove all "ff:ff:ff:ff:ff:ff" entries
    def filter_exists_src_dst_mac_dpid( self ):
        deleteList = []

        for key in self.hashmap_4.keys():
            if "ff:ff:ff:ff:ff:ff" in key:
                deleteList.append( key )

        for key in deleteList:
            self.hashmap_4.pop( key, None)

        return

    def set_dst_dpid( self, i_src_dpid, i_port, i_dst_dpid ):
        self.hashmap_1[ str(i_src_dpid) + str(i_port) ] = i_dst_dpid
        return

    def get_dst_dpid( self, i_src_dpid, i_port ):
        key = str( i_src_dpid ) + str( i_port )

        if key in self.hashmap_1.keys():
            return self.hashmap_1[ key ]
        else:
            return -1

    def get_dst_index( self, i_src_dpid, i_port ):
        dpid = self.get_dst_dpid( i_src_dpid, i_port )

        if dpid != -1:
            return self.get_index( dpid )
        else:
            return -1

    def set_switch_port( self, i_src_index, i_dst_index, i_port ):
        self.links[ i_src_index ][ i_dst_index ] = i_port
        print "set_switch_port: links[ " + repr( i_src_index ) + " ][ " + repr( i_dst_index ) + " ] = " + repr(i_port)
        return

    def get_switch_port( self, i_src_index, i_dst_index ):
        return self.links[ i_src_index ][ i_dst_index ]

    def set_host_port( self, i_mac, i_port ):
        self.hashmap_2[ i_mac ] = i_port
        print "set_host_port: [ " + repr( i_mac ) + " ] -->  " + repr( i_port )  
        return

    def get_host_port( self, i_mac ):
        if i_mac in self.hashmap_2.keys():
            return self.hashmap_2[ i_mac ]
        else:
            return -1

    def set_host_dpid( self, i_mac, i_dpid ):
        self.hashmap_3[ i_mac ] = i_dpid
        print "set_host_switch_dpid: [ " + repr( i_mac ) + " ] -->  " + repr( i_dpid )  
        return        

    def get_host_dpid( self, i_mac ):
        if i_mac in self.hashmap_3.keys():
            return self.hashmap_3[ i_mac ]
        else:
            return -1

    def get_index( self, i_dpid ):
        return self.switches_id.index( i_dpid )

    def get_dpid( self, i_index ):
        return get_dp( i_index ).id

    def get_dp( self, i_index ):
        return self.switches[ int(i_index) ]

    def isConnected( self, i_links ):
        self.connectedData = [ -1 for x in xrange( self.numberOfSwitches ) ]
        self.isConnectedLoop( 0, i_links )

        if -1 not in self.connectedData:
            return True
        else:
            return False;

    def isConnectedLoop( self, i_index, i_links ):
        self.connectedData[ i_index ] = 0

        if i_index >= self.numberOfSwitches - 1:
            return

        for i in range( i_index + 1, self.numberOfSwitches ):
            if i_links[i_index][i] != -1 and self.connectedData[ i ] == -1:
                self.isConnectedLoop( i, i_links )

        return

    def createLinkMatrix( self, i_raw_switches, i_raw_links ):
        # Reset Data
        self.switches = []
        self.switches_id = []
        self.links = []

        # Create Switches Lists
        for switch in i_raw_switches:
            self.switches.append( switch.dp )
            self.switches_id.append( switch.dp.id )

        # Get number of switches
        self.numberOfSwitches = len(self.switches)

        # Init links array ( numberOfSwitches x numberOfSwitches )
        self.links = [[-1 for x in xrange( self.numberOfSwitches )] for y in xrange( self.numberOfSwitches )]

        # add links to the array
        for link in i_raw_links:
            src_dpid = link.src.dpid
            dst_dpid = link.dst.dpid
            src_index = self.switches_id.index( src_dpid )
            dst_index = self.switches_id.index( dst_dpid )
            port = link.src.port_no

            if src_index != -1 and dst_index != -1:
                self.links[src_index][dst_index] = port
                self.set_dst_dpid( src_dpid, port, dst_dpid )

        self.initCounter = self.initCounter + 1

        print "      createLinkMatrix: Done ( " + repr(self.initCounter) + "/" + repr( len(self.switches_id) )  + ' )' 
        return

    def updateLinkMatrix( self, i_src_dpid, i_src_port, status ):
        src_index = get_index( i_src_dpid );
        dst_index = get_dst_index( i_src_dpid, i_src_port )
        port = link.src.port_no

        if dst_index == -1:
            print "updateLinkMatrix: Errorcode 1..."
            return

        if src_index != -1 and dst != -1:
            if status == "Up":
                self.links[src_index][dst_index] = port
            else:
                self.links[src_index][dst_index] = -1

        print "updateLinkMatrix: Done" 
        return

    def printLinkMatrix( self, i_links ):
        result = '\n--------------------------------\n'

        for x in range(0, self.numberOfSwitches ):
            for y in range(0, self.numberOfSwitches ):
                result += '{:4}'.format( i_links[x][y] )
            result += '\n'
        
        result += '--------------------------------\n'

        print result
        return 

    def applyFlowActions( self, i_flow_actions ):
        for i in range(0, len(i_flow_actions)):
            self.applyFlowAction( i_flow_actions[i] )

        return

    def applyFlowAction( self, i_flow_action ):
        if self.printAll:
            print "---------applyFlowAction---------"
            print "    add: " + repr( i_flow_action.isAddMode() )
            print "    rem: " + repr( i_flow_action.isDeleteMode())
            print "    src: " + repr( i_flow_action.get_src_mac() )
            print "    dst: " + repr( i_flow_action.get_dst_mac() )
            print "    port_in: " + repr( i_flow_action.get_port_in() )
            print "    port_out: " + repr( i_flow_action.get_port_out() )
            print "    dpid: " + repr( i_flow_action.get_dp().id )
            print "----------------------------------\n"

        datapath = i_flow_action.get_dp()
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch( in_port = i_flow_action.get_port_in(), eth_dst=i_flow_action.get_dst_mac(), eth_src=i_flow_action.get_src_mac() )
        priority = ofproto.OFP_DEFAULT_PRIORITY

        if i_flow_action.isAddMode():
            actions = []
            port_out = i_flow_action.get_port_out()
            for i in range(0, len(port_out) ):
                actions.append( parser.OFPActionOutput( port_out[i] ) )

            instructions = [ parser.OFPInstructionActions( ofproto.OFPIT_APPLY_ACTIONS, actions ) ]
  
            mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=1,
                datapath=datapath, match=match,
                command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
                priority=priority,
                instructions=instructions)

            datapath.send_msg(mod)
        elif i_flow_action.isDeleteMode():
            command = ofproto.OFPFC_DELETE
            mod = parser.OFPFlowMod( datapath=datapath, match=match, command=command, priority=priority, instructions=[], 
                                     out_port = ofproto.OFPP_ANY, out_group = ofproto.OFPG_ANY )
            datapath.send_msg(mod)
        return        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packetInAction(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src = eth.src
        dst = eth.dst
        port = ev.msg.match['in_port']
        dpid = datapath.id
        buffer_id = msg.buffer_id
        data = msg.data

        if eth.ethertype == ether_types.ETH_TYPE_LLDP: # ignore lldp packet
            return

        # Add Host To Known List
        if self.get_host_port( src ) == -1:
            self.set_host_port( src, port)
            self.set_host_dpid( src, dpid )

        # Prevent Flooding loops...
        if self.exists_src_dst_mac_dpid( repr(src) + " -> " + repr(dst), dpid ):
            if self.get_host_dpid(dst) != -1 and self.get_flow_route_manager_mac( src, dst ) == -1:
                src_index = self.get_index( self.get_host_dpid(src) )
                dst_index = self.get_index( self.get_host_dpid(dst) )

                self.set_flow_route_manager_mac( src, dst, FlowRouteManager( src, dst ) )
                flow_route_manager = self.get_flow_route_manager_mac( src, dst )

                flow_route = self.dijkstra.calculate( src, dst, src_index, dst_index, self.switches, self.switches_id, self.links, self.hashmap_2 )
                self.applyFlowActions( flow_route_manager.install_flow_route_primary( flow_route ) )
                print "packetInAction: New Path: " + repr(src) + " -> " + repr(dst) + " (PRIMARY)"

                if self.mode == "MODE_0":
                    return

                tempLinks = copy.deepcopy(self.links)
                for i in range(0, flow_route.get_length() - 1):
                    temo_src_index = flow_route.get_index(i)
                    temp_dst_index = flow_route.get_index(i+1) 

                    tempLinks[temo_src_index][temp_dst_index] = -1
                    tempLinks[temp_dst_index][temo_src_index] = -1

                if self.isConnected( tempLinks ):
                    flow_route = self.dijkstra.calculate( src, dst, src_index, dst_index, self.switches, self.switches_id, tempLinks, self.hashmap_2 )
                    self.applyFlowActions( flow_route_manager.install_flow_route_secondary( flow_route ) )
                    print "packetInAction: New Path: " + repr(src) + " -> " + repr(dst) + " (SECONDARY)"

                else:
                    print "packetInAction: No Path: " + repr(src) + " -> " + repr(dst) + " (SECONDARY)"

                self.filter_exists_src_dst_mac_dpid()
        
                return
            else:
                return

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        actions = [ datapath.ofproto_parser.OFPActionOutput( ofproto.OFPP_FLOOD, 0 ) ]

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=buffer_id, in_port=port,
            actions=actions, data=data)
        datapath.send_msg(out)

        return

    @set_ev_cls(ofp_event.EventOFPPortStatus)
    def PortChangeAction(self, event):
        src_dpid = event.msg.datapath.id
        port = event.msg.desc.port_no
        state = event.msg.desc.state

        if state & 1 == 0: 
            status = "Up"
        else:                             
            status = "Down"

        src_index = self.get_index(src_dpid)
        dst_index = self.get_dst_index( src_dpid, port )

        if status == "Up": 
            print "PortChangeAction: Switch " + repr(src_dpid) + ", Port " + repr(port) + " is " + status
            self.set_switch_port( src_index, dst_index, port )

            if self.get_switch_port( dst_index, src_index ) != -1:
                flow_route_managers = self.get_flow_route_manager_all()
                for flow_route_manager in flow_route_managers:
                    src_mac = flow_route_manager.get_src_mac()
                    dst_mac = flow_route_manager.get_dst_mac()
                    
                    src_index_final = self.get_index( self.get_host_dpid( src_mac ) )
                    dst_index_final = self.get_index( self.get_host_dpid( dst_mac ) )

                    temp_flow_route = [ flow_route_manager.get_primary_flow_route(), flow_route_manager.get_secondary_flow_route() ]

                    if temp_flow_route[0] == -1:
                        tempLinks = copy.deepcopy(self.links)

                        if temp_flow_route[1] != -1:
                            for i in range(0, temp_flow_route[1].get_length() - 1):
                                temo_src_index = temp_flow_route[1].get_index(i)
                                temp_dst_index = temp_flow_route[1].get_index(i+1) 

                                tempLinks[temo_src_index][temp_dst_index] = -1
                                tempLinks[temp_dst_index][temo_src_index] = -1   

                        if self.isConnected( tempLinks ):
                            flow_route = self.dijkstra.calculate( src_mac, dst_mac, src_index_final, dst_index_final, self.switches, self.switches_id, tempLinks, self.hashmap_2 )
                            self.applyFlowActions( flow_route_manager.install_flow_route_primary( flow_route )  )
                            temp_flow_route[0] = flow_route
                            print "PortChangeAction: New Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (PRIMARY)"
                        else:
                            print "PortChangeAction: No Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (PRIMARY)"

                    if temp_flow_route[1] == -1 and self.mode == "MODE_1":
                        tempLinks = copy.deepcopy(self.links)

                        if temp_flow_route[0] != -1:
                            for i in range(0, temp_flow_route[0].get_length() - 1):
                                temo_src_index = temp_flow_route[0].get_index(i)
                                temp_dst_index = temp_flow_route[0].get_index(i+1) 

                                tempLinks[temo_src_index][temp_dst_index] = -1
                                tempLinks[temp_dst_index][temo_src_index] = -1   

                        if self.isConnected( tempLinks ):
                            flow_route = self.dijkstra.calculate( src_mac, dst_mac, src_index_final, dst_index_final, self.switches, self.switches_id, tempLinks, self.hashmap_2 )
                            self.applyFlowActions( flow_route_manager.install_flow_route_secondary( flow_route )  )
                            temp_flow_route[1] = flow_route
                            print "PortChangeAction: New Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (SECONDARY)"
                        else:
                            print "PortChangeAction: No Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (SECONDARY)"

            return
  
        elif self.get_switch_port( src_index, dst_index ) != -1 and status == "Down":
            print "PortChangeAction: Switch " + repr(src_dpid) + ", Port " + repr(port) + " is " + status 
            self.set_switch_port( src_index, dst_index, -1 )

            if self.get_switch_port( dst_index, src_index ) == -1:
                flow_route_managers = self.get_flow_route_manager_all()
                for flow_route_manager in flow_route_managers:
                    src_mac = flow_route_manager.get_src_mac()
                    dst_mac = flow_route_manager.get_dst_mac()
                    
                    src_index_final = self.get_index( self.get_host_dpid( src_mac ) )
                    dst_index_final = self.get_index( self.get_host_dpid( dst_mac ) )

                    type = [ flow_route_manager.contains_link( src_index, dst_index ), flow_route_manager.contains_link( dst_index, src_index ) ] 

                    if type[0] != "NO_LINK":
                        tempLinks = copy.deepcopy(self.links)
                        temp_flow_route = -1

                        if type[0] == "PRIMARY" and flow_route_manager.get_secondary_flow_route() != -1:
                            temp_flow_route = flow_route_manager.get_secondary_flow_route()
                        if type[0] == "SECONDARY" and flow_route_manager.get_primary_flow_route() != -1:
                            temp_flow_route = flow_route_manager.get_primary_flow_route()

                        if temp_flow_route != -1:   
                            for i in range(0, temp_flow_route.get_length() - 1):
                                temo_src_index = temp_flow_route.get_index(i)
                                temp_dst_index = temp_flow_route.get_index(i+1) 

                                tempLinks[temo_src_index][temp_dst_index] = -1
                                tempLinks[temp_dst_index][temo_src_index] = -1   

                        if self.isConnected( tempLinks ):
                            if not ( type[0] == "SECONDARY" and self.mode == "MODE_0" ):
                                flow_route = self.dijkstra.calculate( src_mac, dst_mac, src_index_final, dst_index_final, self.switches, self.switches_id, tempLinks, self.hashmap_2 )
                                self.applyFlowActions( flow_route_manager.install_flow_route( flow_route, type[0] )  )
                                print "PortChangeAction: New Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (" + type[0] + ")"
                        else:
                            print "PortChangeAction: No Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (" + type[0] + ")"
                            if type[0] == "PRIMARY":
                                self.applyFlowActions( flow_route_manager.clear_primary() )
                            if type[0] == "SECONDARY":
                                self.applyFlowActions( flow_route_manager.clear_secondary() )

                    elif type[1] != "NO_LINK":
                        tempLinks = copy.deepcopy(self.links)
                        temp_flow_route = -1

                        if type[1] == "PRIMARY" and flow_route_manager.get_secondary_flow_route() != -1:
                            temp_flow_route = flow_route_manager.get_secondary_flow_route()
                        if type[1] == "SECONDARY" and flow_route_manager.get_primary_flow_route() != -1:
                            temp_flow_route = flow_route_manager.get_primary_flow_route()

                        if temp_flow_route != -1:   
                            for i in range(0, temp_flow_route.get_length() - 1):
                                temo_src_index = temp_flow_route.get_index(i)
                                temp_dst_index = temp_flow_route.get_index(i+1) 

                                tempLinks[temo_src_index][temp_dst_index] = -1
                                tempLinks[temp_dst_index][temo_src_index] = -1   

                        if self.isConnected(tempLinks):
                            if not ( type[1] == "SECONDARY" and self.mode == "MODE_0" ):
                                flow_route = self.dijkstra.calculate( src_mac, dst_mac, src_index_final, dst_index_final, self.switches, self.switches_id, tempLinks, self.hashmap_2 )
                                self.applyFlowActions( flow_route_manager.install_flow_route( flow_route, type[1] )  )
                                print "PortChangeAction: New Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (" + type[1] + ")"
                        else:
                            print "PortChangeAction: No Path: " + repr(src_mac) + " -> " + repr(dst_mac) + " (" + type[1] + ")"
                            if type[1] == "PRIMARY":
                                self.applyFlowActions( flow_route_manager.clear_primary() )
                            if type[1] == "SECONDARY":
                                self.applyFlowActions( flow_route_manager.clear_secondary() )

        return 
