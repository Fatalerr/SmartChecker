# -*- coding: utf-8 -*-
import re
from tools import read_cmdblock_from_log,MessageLogger
from networkelement import NetworkElement, extract_data
from checker import CheckStatus

__version__ = "v0.5"

command_end_mark = "COMMAND EXECUTED"
logger = MessageLogger('flexins')

class FlexiNS(NetworkElement):
    """Class parse and stroe basic infomation of FlexiNS
example:
    ns = FlexiNS()
    ns.parse_log("log/nsinfo.log")

    print ns.version
    print ns.
    """
    def parse_log(self,logfile):
        loglines = file(logfile).readlines()

        self._data['version'] = _get_ns_version(loglines)

        om_names = ['hostname','c_num','location']
        pat = re.compile("(\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+)")
   
        self._load_data(_get_om_config(loglines),om_names)

    def match_version(self,versions):
        """check if the BU version match the target versions
        
        target_version: a list include some version info. example: ['N5','N6']  
        
        """
        nsversion = self.version.get('BU','')
        if isinstance(versions,list):
            for ver in versions:
                if re.match(ver,nsversion):
                    return True
        else:
            if re.match(versions,nsversion):
                return True
        return False

    def version_in_list(self,version_list):
        """Check if the version in target versions list.
        
        Return:
            (status, info)
        
        status: CheckStatus, one of [VERSION_UNKNOWN,VERSION_MATCHED,VERSION_UNMATCHED]
          info: additional info.     
        """
        #nsversion = self.version.get('BU','')
        if not self.version:
            version_status=(CheckStatus.VERSION_UNKNOWN,"No version info was found.")
        elif self.match_version(version_list):
            version_status=(CheckStatus.VERSION_MATCHED, u"- NS version: %s, 本检查适用于此版本" % self.version['BU']) 
        else:
            version_status=(CheckStatus.VERSION_UNMATCHED,u"- NS version: %s, 本检查不适用与此版本。" % self.version['BU'])
        
        return version_status
    
    def __repr__(self):
        if 'c_num' in self._data:
            _reprtxt = "FlexiNS(hostname:%(hostname)s,C_NUM:%(c_num)s)"
        else:
            _reprtxt = "FlexiNS(hostname:%(hostname)s)"

        return _reprtxt % self._data
 

def _get_ns_version(loglines):
    """This function will parse the FlexiNS version info from log lines.
    Arguments:
        loglines   log lines
    Return:
        return  a dict include package's status and id info or an empty dict.
    
    example: {'BU': 'N5 1.17-5', 'FB': 'N5 1.17-5', 'NW': 'N4 1.19-2', 'UT': 'N4 1.19-2'}
    
    """
    pkgid_pat = re.compile("\s+(BU|FB|NW)\s+.*?\n\s+(\w\d [\d\.-]+)")

    logtxt = read_cmdblock_from_log(loglines,'WQO:CR;',command_end_mark)
    pkgids = pkgid_pat.findall(logtxt)
    if not pkgids:
        logger.error("Package ID not found in log: %s")
        return None

    return dict(pkgids)

def _get_om_config(loglines):
    """extract the om config from the loglines 
    Arguments:
        loglines  log lines for analysis.
    Return:
        a dict include the config_names: ['conn','type','sw_level','cnum','hostname','location']
    example: 
        {'cnum': '400248', 'hostname': 'NCMME30BNK', 'sw_level': '5', 'location': 'NC_HGT3F_M03', 'type': 'DX220', 'conn': '000'}
    """
    config_names = ['conn','type','sw_level','c_num','hostname','location']
    pat = re.compile("(\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+)")

    logtxt = read_cmdblock_from_log(loglines,'QNI',command_end_mark)
    r = pat.search(logtxt)
    if r:
        return dict(zip(config_names,r.groups()))
    else:
        return None


def get_ns_version(configlog):
	"""This function will parse the NS version info from logfile.
	Input  logfile
	return  a tuple include (ns_version)
	example: ('N5 1.19-3', 'N5 1.17-5','UNKNOWN')
	"""
	version = None
	#search the version info , the real version as default is mark with 'Y' in 'DEF' column
	version_pat = re.compile(r"ZWQO.*?      Y    Y",re.S)

	try:	
		log = ''.join(file(configlog).readlines())
        
		r=version_pat.search(log)
		if r:
			logpos=r.end()
			#version info is the line between pos:30--43
			version = log[logpos+30:logpos+43]
			
		return version
				
	except IOError,e:
		logger.info("IOError: %s" % e)
		return 'UNKNOWN'
		
