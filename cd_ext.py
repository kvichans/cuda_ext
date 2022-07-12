''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky   (kvichans on github.com)
    Alexey Torgashin    (CudaText)
Version:
    '1.7.44 2022-07-12'
ToDo: (see end of file)
'''
import  re, os, sys, json, time, traceback, unicodedata
from    fnmatch         import fnmatch

import          cudatext            as app
from            cudatext        import ed
from            cudatext_keys   import *
import          cudatext_cmd        as cmds
import          cudax_lib           as apx

from            .cd_kv_base     import *        # as part of this plugin
from            .cd_kv_dlg      import *        # as part of this plugin
#try:    from    cuda_kv_base    import *    # as separated plugin
#except: from     .cd_kv_base    import *    # as part of this plugin
#try:    from    cuda_kv_dlg     import *    # as separated plugin
#except: from     .cd_kv_dlg     import *    # as part of this plugin
try:
    _   = get_translation(__file__)
except:
    _   = lambda p:p

d       = dict

FROM_API_VERSION    = '1.0.119'
FROM_API_VERSION    = '1.0.182'     # PROC_SPLITTER_GET/SET, LOG_CONSOLE_GET_MEMO_LINES

ONLY_SINGLE_CRT     = _("{} doesn't work with multi-carets")
ONLY_FOR_NO_SEL     = _("{} works when no selection")
NO_PAIR_BRACKET     = _("Cannot find matching bracket for '{}'")
NO_FILE_FOR_OPEN    = _("Cannot open: {}")
NEED_UPDATE         = _("Need to update CudaText")

pass;                           # Logging
pass;                           from pprint import pformat
pass;                           pfrm100=lambda d:pformat(d,width=100)
pass;                           LOG = (-2== 2)  # Do or dont logging.
pass;                           ##!! waits correction

#C1      = chr(1)
GAP     = 5

def _get_filename(_ed):
    fn  = _ed.get_filename()
    if fn=='?':     # Not text content
        fn  = _ed.get_filename('*') if app.app_api_version()>='1.0.287' else ''
    return fn
   #def _get_filename

def _file_open(op_file):
    if not app.file_open(op_file):
        return None
    for h in app.ed_handles():
        op_ed   = app.Editor(h)
        if _get_filename(op_ed) and os.path.samefile(op_file, _get_filename(op_ed)):
            return op_ed
    return None
   #def _file_open

def dlg_menu(how, its='', sel=0, cap='', clip=0, w=0, h=0, opts_key=''):
    if opts_key:
        def fit_bit(val, key, bit):
            opt = apx.get_opt(key, None)
            if opt is None: return val
            if opt:         return val | bit
            else:           return val & ~bit
        how = fit_bit(how, f'{opts_key}.menu.no_fuzzy', app.DMENU_NO_FUZZY  )
        how = fit_bit(how, f'{opts_key}.menu.centered', app.DMENU_CENTERED  )
        how = fit_bit(how, f'{opts_key}.menu.monofont', app.DMENU_EDITORFONT)
    api = app.app_api_version()
#   if api<='1.0.193':  #  list/tuple, focused(?), caption
#   if api<='1.0.233':  #  MENU_NO_FUZZY, MENU_NO_FULLFILTER
#   if api<='1.0.275':  #  MENU_CENTERED
    if api<='1.0.334':  #  clip, w, h
        return  app.dlg_menu(how, its, focused=sel, caption=cap)
#   if api<='1.0.346':  #  MENU_EDITORFONT
    return      app.dlg_menu(how, its, focused=sel, caption=cap, clip=clip, w=w, h=h)
   #def dlg_menu

#############################################################
class SCBs:
    @staticmethod
    def copy_term():
        """ Find and copy to CB word or 'smth'/"smth"/[smth] near/around caret.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
        """
        term,(bgn,end) = SCBs._parseTerm(ed)
        pass;                  #LOG and log('term,(bgn,end)={}',(term,(bgn,end)))
        pass;                  #LOG and log('test={}',(ed.get_text_line(ed.get_carets()[0][1])[bgn:end]))
        if term:
            app.app_proc(app.PROC_SET_CLIP, term)
            app.msg_status(f(_('Copy {}'), repr(term[:50])))
       #def copy_term

    @staticmethod
    def replace_term():
        """ Find a word or 'smth'/"smth"/[smth] near/around caret 
                and replace with CB-clip.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
        """
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip:    return app.msg_status(_('No clip'))
        term,(bgn,end) = SCBs._parseTerm(ed)
        pass;                  #LOG and log('term,(bgn,end)={}',(term,(bgn,end)))
        pass;                  #LOG and log('test={}',(ed.get_text_line(ed.get_carets()[0][1])[bgn:end]))
        if term:
            row = ed.get_carets()[0][1]
            line= ed.get_text_line(row)
            line= line[:bgn] + clip + line[end:]
            ed.set_text_line(row, line)
            app.msg_status(f(_('Replace {} with clip'), repr(term[:50])))
       #def replace_term

    lexer       = None
    wrdchs      = ''
    wrdcs_re    = None
    quotes      = ''
    brckts      = ''
    opn2cls     = {}
    cls2opn     = {}
    allspec     = ''
    notspec_re  = None
    signs       = ''
    signs_re    = None
    @staticmethod
    def _prep_static_data():
        lexer           = ed.get_prop(app.PROP_LEXER_FILE)
        if SCBs.lexer==lexer and SCBs.quotes: return
        SCBs.wrdchs     = apx.get_opt('word_chars', '') + '_'
        SCBs.wrdcs_re   = re.compile(r'^[\w'+re.escape(SCBs.wrdchs)+']+')
        SCBs.quotes     = apx.get_opt('cudaext_quotes', '"'+"'`")
        SCBs.brckts     = apx.get_opt('cudaext_brackets', '[](){}<>')
        SCBs.opn2cls    = {SCBs.brckts[i  ]:SCBs.brckts[i+1] for i in range(0,len(SCBs.brckts),2)}
        SCBs.cls2opn    = {SCBs.brckts[i+1]:SCBs.brckts[i  ] for i in range(0,len(SCBs.brckts),2)}
        SCBs.allspec    = SCBs.wrdchs + SCBs.quotes + SCBs.brckts
        SCBs.notspec_re = re.compile(r'^[\W'+re.escape(SCBs.allspec)+']+')
        SCBs.signs      = apx.get_opt('cudaext_signs', r'!@#$%^&*-=+;:\|,./?`~')
        SCBs.signs_re   = re.compile(r'^['+re.escape(SCBs.signs)+']+')
       #def _prep_static_data

    @staticmethod
    def _parseTerm(ted=ed, ops={}):         #NOTE: _parseTerm
        """ Find _term_ around caret *into* current line.
            Parse only (in parse order)
                ·a|c·      abc|·   ·|abc        "word"-chars are \w             · is [^\w_]
                'abc'|·    ·|"abc"              any quotes from "" ''           · is [^\w_]
                [abc]|·    ·|(abc)              any brackets from [](){}<>      · is [^\w_'"]
            Params from def/user/lex
                word_chars          (no)        Append chars to \w
                cudaext_quotes      '"`         Using quotes 
                cudaext_brackets    [](){}<>    Using brackets
            Params
                ted     (ed)
                ops     dict({})    
                    only_word:False             Detect only term as "word"
            Return      
                term, col_brn, col_end          term = line[col_bgn:col_end]
        """
        NONE    = None, (None, None)
        crts    = ted.get_carets()
        if len(crts)>1:
            app.msg_status(_("Command doesn't work with multi-carets"))
            return NONE
        (cCrt, rCrt
        ,cEnd, rEnd)= crts[0]
        if cEnd!=-1:
            app.msg_status(_('Command works when no selection'))
            return NONE
        SCBs._prep_static_data()
        word_b  = ops.get('only_word', False)
        
        line    = ted.get_text_line(rCrt)
        c_crt   = cCrt

        c_aft   = line[c_crt]   if c_crt<len(line) else ' '
        c_bfr   = line[c_crt-1] if c_crt>0         else ' '
        pass;                  #LOG and log('c_crt,(c_bfr,c_aft),line={}',(c_crt,(c_bfr,c_aft),line))
        if      word_b \
        and not (c_bfr.isalnum() or c_bfr in SCBs.wrdchs) \
        and not (c_aft.isalnum() or c_aft in SCBs.wrdchs) :
            pass;              #LOG and log('for word unk bfr+aft',())
            return NONE
        if not word_b \
        and not (c_bfr.isalnum() or c_bfr in SCBs.quotes or c_bfr in SCBs.brckts) \
        and not (c_aft.isalnum() or c_aft in SCBs.quotes or c_aft in SCBs.brckts) :
            pass;              #LOG and log('for expr unk bfr+aft',())
            return NONE
        
        # Detect word
        if      (c_bfr.isalnum() or c_bfr in SCBs.wrdchs) \
        or      (c_aft.isalnum() or c_aft in SCBs.wrdchs) :
            pass;              #LOG and log('?? for word',())
            tx_bfr  = line[:c_crt]
            tx_aft  = line[ c_crt:]
            pass;              #LOG and log('tx_bfr,tx_aft={}',(tx_bfr,tx_aft))
            gp_aft  = 0
            gp_bfr  = 0
            if (c_bfr.isalnum() or c_bfr in SCBs.wrdchs):   # abc|
                tx_bfr_r= ''.join(reversed(tx_bfr))
                gp_bfr  = len(SCBs.wrdcs_re.search(tx_bfr_r).group())
            if (c_aft.isalnum() or c_aft in SCBs.wrdchs):   # |abc
                gp_aft  = len(SCBs.wrdcs_re.search(tx_aft  ).group())
            pass;              #LOG and log('gp_bfr,gp_aft={}',(gp_bfr,gp_aft))
            return line[c_crt-gp_bfr:c_crt+gp_aft], (c_crt-gp_bfr, c_crt+gp_aft)
        assert not word_b

        find_prms = None
        rfind_prms= None
        gap_crt     = 0
        if False:pass
        # Detect qouted
        elif c_bfr in SCBs.quotes and line.count(c_bfr, c_crt)%2==0:    #   'abc'|
            rfind_prms  = c_bfr, 0, c_crt-2
            gap_crt     = 0
        elif c_bfr in SCBs.quotes and line.count(c_bfr, c_crt)%2==1:    #   '|abc'
            find_prms   = c_bfr, c_crt
            gap_crt     = -1
        elif c_aft in SCBs.quotes and line.count(c_aft, c_crt)%2==0:    #   |'abc'
            find_prms   = c_aft, c_crt+1
            gap_crt     = 0
        elif c_aft in SCBs.quotes and line.count(c_aft, c_crt)%2==1:    #   'abc|'
            rfind_prms  = c_aft, 0, c_crt-1
            gap_crt     = 1
        # Detect brackets
        elif c_bfr in SCBs.cls2opn:                                     #   [...]|
            rfind_prms  = SCBs.cls2opn[c_bfr], 0, c_crt-2
            gap_crt     = 0
        elif c_bfr in SCBs.opn2cls:                                     #   [|..]
            find_prms   = SCBs.opn2cls[c_bfr], c_crt
            gap_crt     = -1
        elif c_aft in SCBs.opn2cls:                                     #   |[...]
            find_prms   = SCBs.opn2cls[c_aft], c_crt+1
            gap_crt     = 0
        elif c_aft in SCBs.cls2opn:                                     #   [..|]
            rfind_prms  = SCBs.cls2opn[c_aft], 0, c_crt-1
            gap_crt     = 1
        pass;                  #LOG and log('(rfind_prms,find_prms),gap_crt={}',((rfind_prms,find_prms),gap_crt))
        if rfind_prms:
            trm_bgn = line.rfind(*rfind_prms)
            pass;              #LOG and log('trm_bgn={}',(trm_bgn))
            return line[trm_bgn:c_crt+gap_crt          ], (trm_bgn      , c_crt+gap_crt)  if -1!=trm_bgn else NONE
        if find_prms:
            trm_end = line.find(*find_prms)
            pass;              #LOG and log('trm_end={}',(trm_end))
            return line[        c_crt+gap_crt:trm_end+1], (c_crt+gap_crt, trm_end+1    )  if -1!=trm_end else NONE
        return NONE
        #def _parseTerm

    @staticmethod
    def expand_sel(copy=False):
        """ Expand current selection to the nearest usefull state:
                caret -> word -> phrase in brakets/quotes -> phrase with brakets/quotes -> ...
            Example. | caret, <...> selection
                fun('smt and oth', par)
                fun('smt an|d oth', par)
                fun('smt <and> oth', par)
                fun('smt< and >oth', par)
                fun('<smt and oth>', par)
                fun(<'smt and oth'>, par)
                fun(<'smt and oth', par>)
                fun<('smt and oth', par)>
                <fun('smt and oth', par)>
            Params
                copy    Copy new (only changed) selected text to clipboard
            Return  
                        Selection is changed
        """
        pass;                  #LOG and log('copy={}',(copy))
        crts    = ed.get_carets()
        if len(crts)>1:
            app.msg_status(_("Command doesn't work with multi-carets"))
            return False
        SCBs._prep_static_data()
        def get_char_before(col, row, dfval):
            """ Get first not EOL char """
            line    = ed.get_text_line(row)
            if col>0:           return line[col-1], col      -1, row
            return dfval, 0, row
#           while row>0:
#               row -= 1
#               line= ed.get_text_line(row)
#               if line:        return line[   -1], len(line)-1, row
            return dfval, -1, -1
        def get_char_after(col, row, dfval):
            """ Get first not EOL char """
            line    = ed.get_text_line(row)
            if col<len(line)-1: return line[col+1], col+1, row
            return dfval, len(line), row
#           while row<ed.get_line_count()-1:
#               row += 1
#               line= ed.get_text_line(row)
#               if line:        return line[    0], 0,     row
            return dfval, -1, -1
        
        (cCrt, rCrt
        ,cEnd, rEnd)    = crts[0]
        if -1==rEnd:
            cEnd, rEnd  = cCrt, rCrt
        def set_sel(cSelBgn, rSelBgn, cSelEnd, rSelEnd):
            if (rCrt, cCrt) >= (rEnd, cEnd):
                ed.set_caret(cSelEnd, rSelEnd, cSelBgn, rSelBgn)
            else:
                ed.set_caret(cSelBgn, rSelBgn, cSelEnd, rSelEnd)
            if copy:
                sSel    = ed.get_text_sel()
                app.app_proc(app.PROC_SET_CLIP, sSel)
                return True
        ((rSelB, cSelB)
        ,(rSelE, cSelE))= apx.minmax((rCrt, cCrt), (rEnd, cEnd))
        cSelE          -= 1                 ##??
#       sSel            = ed.get_text_sel()
        pass;                  #LOG and log('(rSelB, cSelB),(rSelE, cSelE),sSel={}',((rSelB, cSelB),(rSelE, cSelE),sSel[:50]))
        sBfr,cBfr,rBfr  = get_char_before(cSelB, rSelB, ' ')
        sAft,cAft,rAft  = get_char_after( cSelE, rSelE, ' ')
        pass;                  #LOG and log('(sBfr,rBfr,cBfr),(sAft,rAft,cAft)={}',((sBfr,rBfr,cBfr),(sAft,rAft,cAft)))
        
        # Try to expand from '|smth|' to |'smth'| or from (|smth|) to |(smth|)
        pass;                  #LOG and log('sBfr==sAft and sBfr in SCBs.quotes={}',(sBfr==sAft and sBfr in SCBs.quotes))
        pass;                  #LOG and log('sBfr==SCBs.cls2opn.get(sAft)={}',(sBfr==SCBs.cls2opn.get(sAft)))
        if  sBfr and sAft and \
        (   sBfr==sAft and sBfr in SCBs.quotes
        or  sBfr==SCBs.cls2opn.get(sAft) ):
            pass;              #LOG and log('|smth| --> |"smth"| or from (|smth|) to |(smth)|',())
            return      set_sel(cBfr, rBfr, cAft+1, rAft)
            

        # Try to expand from (|smth| to (|smth...|) or |smth|) to (|...smth|)
        if  sBfr in SCBs.opn2cls:
            c_opn,c_cls,\
            cAft,rAft   = fnd_mtch_char(ed, sBfr, SCBs.opn2cls[sBfr], ed.get_text_line(rBfr), cBfr+1, rBfr, to_end=True)
            pass;              #LOG and log('c_opn, c_cls, cAft, rAft={}',(c_opn, c_cls, cAft, rAft))
            if -1!=rAft:
                pass;          #LOG and log('(|smth| --> (|smth...|)',())   #)
                return  set_sel(cSelB, rSelB, cAft, rAft)
        if  sAft in SCBs.cls2opn:
            c_opn,c_cls,\
            cBfr,rBfr   = fnd_mtch_char(ed, sAft, SCBs.cls2opn[sAft], ed.get_text_line(rAft), cAft-1, rAft, to_end=False)
            pass;              #LOG and log('c_opn, c_cls, cBfr,rBfr={}',(c_opn, c_cls, cBfr,rBfr))
            if -1!=rBfr:
                pass;          #LOG and log('|smth|) --> (|...smth|)',())   #(
                return  set_sel(cBfr+1, rBfr, cSelE+1, rSelE)
        
        # Try to expand from |smth|( to |smth(...)| or )|smth| to |(...)smth|
        if  sBfr in SCBs.cls2opn:
            c_opn,c_cls,\
            cBfr,rBfr   = fnd_mtch_char(ed, sBfr, SCBs.cls2opn[sBfr], ed.get_text_line(rBfr), cBfr-1, rBfr, to_end=False)
            pass;              #LOG and log('c_opn, c_cls, cBfr,rBfr={}',(c_opn, c_cls, cBfr,rBfr))
            if -1!=rBfr:
                pass;          #LOG and log(')|smth| --> |(...)smth|',())   #)
                return  set_sel(cBfr, rBfr, cSelE+1, rSelE)
        if  sAft in SCBs.opn2cls:
            c_opn,c_cls,\
            cAft,rAft   = fnd_mtch_char(ed, sAft, SCBs.opn2cls[sAft], ed.get_text_line(rAft), cAft+1, rAft, to_end=True)
            pass;              #LOG and log('c_opn, c_cls, cAft, rAft={}',(c_opn, c_cls, cAft, rAft))
            if -1!=rBfr:
                pass;          #LOG and log('|smth|( --> |smth(...)|',())   #(
                return  set_sel(cSelB, rSelB, cAft+1, rAft)
        
        # Try to expand from "|smth| smth" to "|smth smth|"
        if  sBfr in SCBs.quotes:
            line    = ed.get_text_line(rSelB)
            cNewE   = line.find(sBfr, cSelE+1)
            if -1!=cNewE:
                pass;          #LOG and log('"|smth| smth" --> "|smth smth|"',())
                return  set_sel(cSelB, rSelB, cNewE, rSelB)
        if  sAft in SCBs.quotes:
            line    = ed.get_text_line(rSelE)
            cNewB   = line.rfind(sAft, 0, cSelB)
            if -1!=cNewB:
                pass;          #LOG and log('"smth |smth|" --> "|smth smth|"',())
                return  set_sel(cNewB+1, rSelB, cSelB, rSelB)
        
        # Try to expand from |smth| to |ABCsmthXYX|
        sBfrTxR = ''
        nBfrGap = 0
        nAftGap = 0
        if  sBfr in SCBs.wrdchs or sBfr.isalnum() \
        or  sAft in SCBs.wrdchs or sAft.isalnum():
            if  sBfr in SCBs.wrdchs or sBfr.isalnum():
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.wrdcs_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft in SCBs.wrdchs or sAft.isalnum():
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.wrdcs_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |ABCsmthXYX|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)
        
        # Try to expand from |smth| to |.smth,|
        nBfrGap = 0
        nAftGap = 0
        if      sBfr in SCBs.signs\
        or      sAft in SCBs.signs :   #NOTE: do
            if  sBfr in SCBs.signs:
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.signs_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft in SCBs.signs:
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.signs_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |.smth,|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)

        # Try to expand from |smth| to |·smth·|
        assert not sBfr.isalnum() and not sAft.isalnum()
        nBfrGap = 0
        nAftGap = 0
        if      sBfr not in SCBs.allspec \
        or      sAft not in SCBs.allspec :
            if  sBfr not in SCBs.allspec:
                sBfrLn  = ed.get_text_line(rBfr)
                sBfrTx  = sBfrLn[:cBfr]
                sBfrTxR = ''.join(reversed(sBfrTx)) if not sBfrTxR else sBfrTxR
                oBfrMch = SCBs.notspec_re.search(sBfrTxR)
                nBfrGap = len(oBfrMch.group()) if oBfrMch else 0
                pass;          #LOG and log('nBfrGap={}',(nBfrGap))
            else:
                nBfrGap = -1
            if  sAft not in SCBs.allspec:
                sAftLn  = ed.get_text_line(rAft)
                sAftTx  = sAftLn[cAft:]
                oAftMch = SCBs.notspec_re.search(sAftTx)
                nAftGap = len(oAftMch.group()) if oAftMch else 0
                pass;          #LOG and log('nAftGap={}',(nAftGap))
            pass;              #LOG and log('|smth| to |·smth·|',())
            return      set_sel(cBfr-nBfrGap, rBfr, cAft+nAftGap, rAft)
        return False
       #def expand_sel

#  #class SCBs

#############################################################
class Jumps_cmds:
    @staticmethod
    def scroll_to(place):
        wrapped         = ed.get_prop(app.PROP_WRAP)!=0
        if place in ('cen', 'top', 'bot') and     wrapped:
            # Alex: github.com/kvichans/cuda_ext/issues/119#issue-386725583
            def get_pos(y, scr_lines):
                if   place=='cen':
                    return max(0, y-scr_lines//2)
                elif place=='top':
                    return y
                elif place=='bot':
                    return max(0, y-scr_lines+1)

            x, y, x1, y1= ed.get_carets()[0]
            scr_lines   = ed.get_prop(app.PROP_VISIBLE_LINES)
            new_scrl    = get_pos(y, scr_lines)

            wrapinfo    = ed.get_wrapinfo()
            for n in reversed(range(len(wrapinfo))):
                wi      = wrapinfo[n]
                if wi['line']==y and wi['char']-1<=x:
                    new_scrl = get_pos(n, scr_lines)
                    break

            ed.set_prop(app.PROP_SCROLL_VERT, new_scrl)
            return 
            
        if place in ('cen', 'top', 'bot') and not wrapped:
            txt_lines   = ed.get_line_count()
            old_top_line= ed.get_prop(app.PROP_LINE_TOP) if app.app_api_version()>='1.0.126' else ed.get_top()
            scr_lines   = ed.get_prop(app.PROP_VISIBLE_LINES)
            crt_line    = ed.get_carets()[0][1]
            vert_indent = apx.get_opt('cuda_ext_vert_indent', 0)
#           vert_indent = abs(apx.get_opt('find_indent_vert', 0))
        
            new_top_line= old_top_line
            if False:pass
            elif place=='cen':
                new_top_line= crt_line - int(scr_lines/2)
            elif place=='top':
                new_top_line= crt_line              - vert_indent
            elif place=='bot':
                new_top_line= crt_line - scr_lines  + vert_indent+1
            new_top_line= max(new_top_line, 0)
            new_top_line= min(new_top_line, txt_lines-1)
            pass;              #LOG and log('cur, old, new, scr, ind={}',(crt_line, old_top_line, new_top_line, scr_lines, vert_indent))
        
            if new_top_line!=old_top_line:
                if app.app_api_version()>='1.0.126':
                    ed.set_prop(app.PROP_LINE_TOP, str(new_top_line))
                else: # old
                    ed.set_top(new_top_line)
            return 

        if place in ('lf', 'rt') and not wrapped:
            free_crt    = apx.get_opt('caret_after_end', False)
            move_crt    = apx.get_opt('cuda_ext_horz_scroll_move_caret', False)
            shift       = apx.get_opt('cuda_ext_horz_scroll_size', 30)
#           old_lf_col  = ed.get_prop(app.PROP_COLUMN_LEFT)
            old_lf_col  = ed.get_prop(app.PROP_SCROLL_HORZ)
            
            new_lf_col  = old_lf_col + (-shift if place=='lf' else shift)
            new_lf_col  = max(new_lf_col, 0)
            pass;              #LOG and log('cols,old_l,new_l={}',(old_lf_col,new_lf_col))
            if new_lf_col==old_lf_col:                          return # Good state
#           ed.set_prop(app.PROP_COLUMN_LEFT, str(new_lf_col))
            ed.set_prop(app.PROP_SCROLL_HORZ, str(new_lf_col))
            
            if not (free_crt and move_crt):                     return # No need opts
            # Move caret if it isnot shown
            crts        = ed.get_carets()
            if len(crts)>1:                                     return # M-carets
            if crts[0][2]!=-1:                                  return # With sel
            old_crt_pos,y   = crts[0][0], crts[0][1]
            old_crt_col,y   = ed.convert(app.CONVERT_CHAR_TO_COL, old_crt_pos, y)
            scr_cols        = ed.get_prop(app.PROP_VISIBLE_COLUMNS)
            if new_lf_col<=old_crt_col<(new_lf_col+scr_cols):   return # Visible
            new_crt_col     = new_lf_col + (old_crt_col-old_lf_col)
            new_crt_col     = min(max(new_crt_col, 0), new_lf_col + scr_cols)
            new_crt_pos,y   = ed.convert(app.CONVERT_COL_TO_CHAR, new_crt_col, y)
            pass;              #LOG and log('old_p,old_c,new_c,new_p={}',(old_crt_pos,old_crt_col,new_crt_col,new_crt_pos))
            ed.set_caret(new_crt_pos,y)
       #def scroll_to

    @staticmethod
    def jump_to_matching_bracket():
        ''' Jump single (only!) caret to matching bracket.
            Pairs: [] {} () <> «»
        '''
        pass;                      #LOG and log('')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:
            return app.msg_status(ONLY_FOR_NO_SEL.format(_('Command')))

        (c_opn, c_cls
        ,col, row)  = find_matching_char(ed, cCrt, rCrt)

        if c_opn!='' and -1!=col:
            pass;                  #LOG and log('set_caret(col, row)={}', (col, row))
            ed.set_caret(col, row)
        else:
            return app.msg_status(NO_PAIR_BRACKET.format(c_opn))
       #def jump_to_matching_bracket

    @staticmethod
    def jump_to_status_line(status, nx_pr, bgn_end):
        pass;                  #LOG and log('status, nx_pr, bgn_end={}',(status, nx_pr, bgn_end))
        trg_sts = [app.LINESTATE_SAVED  ]   if status=='svd' else \
                  [app.LINESTATE_CHANGED
                  ,app.LINESTATE_ADDED  ]   if status=='mod' else \
                  [app.LINESTATE_CHANGED
                  ,app.LINESTATE_SAVED
                  ,app.LINESTATE_ADDED  ]   if status=='wrk' else \
                  [app.LINESTATE_NORMAL ]
        step    = (-1 if nx_pr=='prev' else 1)
        fini_r  = ( 0 if nx_pr=='prev' else ed.get_line_count()-1)
        init_r  = ed.get_carets()[0][1]                             # Start from upper caret (not selection)
        init_st = ed.get_prop(app.PROP_LINE_STATE, init_r)          # Start status
        pass;                  #LOG and log('step,init_r,fini_r,trg_sts={}',(step,init_r,fini_r,trg_sts))
        
        trgt_r  = -1
        state   = 'to-free' if init_st in trg_sts else 'to-trgt'
        test_r  = init_r
        while True:
            test_r += step
            if test_r==fini_r: break#while
            test_st = ed.get_prop(app.PROP_LINE_STATE, test_r)
            pass;              #LOG and log('state,test_r,test_st={}',(state,test_r,test_st))
            if False:pass
            elif state == 'to-free' and test_st     in trg_sts:     #   in init wrk fragment
                pass
            elif state == 'to-free' and test_st not in trg_sts:     # exit init wrk fragment
                state   = 'to-trgt'
            elif state == 'to-trgt' and test_st not in trg_sts:     #   in free space
                state   = 'to-trgt'
            elif state == 'to-trgt' and test_st     in trg_sts:     # found
                trgt_r  = test_r
                if nx_pr=='next' and bgn_end=='bgn' or \
                   nx_pr=='prev' and bgn_end=='end': break#while    # true side of fragment
                state   = 'to-side'
            elif state == 'to-side' and test_st     in trg_sts:     #   in trgt fragment
                trgt_r  = test_r
            elif state == 'to-side' and test_st not in trg_sts:     # exit trgt fragment
                break#while
        
        if -1==trgt_r:  return app.msg_status(_("Not found lines by status"))
        ed.set_caret(0, trgt_r)
       #def jump_to_status_line
       
    @staticmethod
    def jump_to_line_by_cb():
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        row = -1
        try:    row = int(clip)-1
        except: return  app.msg_status(_("No line number in clipboard"))
        if not (0 <= row < ed.get_line_count()):
            return      app.msg_status(f(_("No line #{}"), row))
        ed.set_caret(0, row)
       #def jump_to_line_by_cb
       
    @staticmethod
    def jump_ccsc(drct='l', sel=False):
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        core_cmds   = { ('r', False): cmds.cCommand_GotoWordNext
                      , ('l', False): cmds.cCommand_GotoWordPrev
                      , ('r', True ): cmds.cCommand_GotoWordNext_Sel
                      , ('l', True ): cmds.cCommand_GotoWordPrev_Sel
                      }
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        line        = ed.get_text_line(rCrt)
        use_core    = ( drct=='l' and cCrt==0
                    or  drct=='l' and not re.search(r'\w', line[cCrt-1])
                    or  drct=='r' and cCrt>=len(line)
                    or  drct=='r' and not re.search(r'\w', line[cCrt])
                      )
        if use_core:    return ed.cmd(core_cmds[drct, sel])
        
        # Extract tail of word
        tail    = line[cCrt:] \
                    if drct=='r' else \
                  ''.join(reversed(line[:cCrt]))
        pass;                  #LOG and log('tail={}',(tail))
        tail    = re.search(r'\w+', tail).group()
        pass;                  #LOG and log('tail={}',(tail))
        
        # Scan to nearest aCamelCase or "_" in snake_case_case test___test___dd ddTest____DD__DDddd_test
        gap     = 0
        for pos, ch in enumerate(tail):
            if pos>0 and ch!='_' and ch==ch.upper():
                # Skip first and stop at next Camel
                gap = pos + (1 if drct=='l' else 0)     # For backward stop after C, for forward - before
                break
            if drct=='r' and ch=='_' and (pos+1)<len(tail) and tail[pos+1]!='_':
                # For forward stop after _
                gap = pos+1
                break
            if drct=='l' and ch!='_' and (pos+1)<len(tail) and tail[pos+1]=='_':
                # For backward stop before _
                gap = pos+1
                break
        pass;                  #LOG and log('gap={}',(gap))
        if gap==0:    return ed.cmd(core_cmds[drct, sel])
        gap     = gap if drct=='r' else -gap
        
        # Jump
        if not sel:
            ed.set_caret(cCrt + gap, rCrt)
        else:
            cEnd, rEnd  = (cCrt, rCrt) if cEnd==-1 else (cEnd, rEnd)
            ed.set_caret(cCrt + gap, rCrt, cEnd, rEnd)
       #def jump_ccsc
 
    @staticmethod
    def jump_staple(what):
        """ Move a caret along the nearest left staple """ 
        crts    = ed.get_carets()
        if len(crts)>1:     return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        if cEnd!=-1:        return app.msg_status(ONLY_FOR_NO_SEL.format(_('Command')))
            
        folds   = ed.folding(app.FOLDING_GET_LIST) \
                    if app.app_api_version() < '1.0.265' else \
                  ed.folding(app.FOLDING_GET_LIST_FILTERED, item_y=rCrt, item_y2=rCrt)
        if not folds:       return app.msg_status(_('No staple to jump'))
        crt_r, crt_x, crt_c = rCrt, cCrt, ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]
        pass;                  #log('what, crt_r, crt_x, crt_c={}', (what,crt_r, crt_x, crt_c))
        pass;                  #log('folds={}', (folds))
        folds   = [(y, y2, x) for (y, y2, x, staple, folded) 
                    in folds 
                    if  staple and not folded
                    and y<=crt_r<=y2
                  ]
        pass;                  #log('folds={}', (folds))
        if not folds:       return app.msg_status(_('No staple to jump'))
        best_yyс= None
        for y,y2,stp_x in folds:
            if True: #stp_x==0:
                line_y  = ed.get_text_line(y)
                stp_x   = len(line_y) - len(line_y.lstrip())                # Count of start blanks
            stp_c       = ed.convert(app.CONVERT_CHAR_TO_COL, stp_x, y)[0]  # Column of staple
            best_yyс= (y,y2,stp_c) \
                        if stp_c <= crt_c and (not best_yyс or stp_c > best_yyс[2]) else \
                      best_yyс
            pass;              #log('y,y2,stp_x,stp_c,best_yyс={}', ((y,y2),(stp_x,stp_c),best_yyс))
        if not best_yyс:    return app.msg_status(_('No staple to jump'))
        new_r   = best_yyс[0 if what=='bgn' else 1]
        if new_r==crt_r:    return
        new_x   = ed.convert(app.CONVERT_COL_TO_CHAR, crt_c, new_r)[0]
        pass;                  #log('new_x, new_r={}', (new_x, new_r))
        ed.set_caret(new_x, new_r)
       #def jump_staple
 
    @staticmethod
    def dlg_bms_in_tab():
        bm_lns  = ed.bookmark(app.BOOKMARK_GET_LIST, 0)
        bm_lns  = [bm for bm in bm_lns if ed.bookmark(app.BOOKMARK_GET_PROP, bm)]   # Skip hidden
        if not bm_lns:  return app.msg_status(_('No bookmarks'))
        pass;                  #log("bm_lns={}",(bm_lns))
        tab_sps = ' '*ed.get_prop(app.PROP_TAB_SIZE)
        bms     = [ (line_num                                               # line number
                    ,ed.get_text_line(line_num).replace('\t', tab_sps)      # line string
                    ,ed.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']   # kind of bm
                    )   for line_num in bm_lns]
        pass;                  #LOG and log('bms=¶{}',pf(bms))
        rCrt    = ed.get_carets()[0][1]
        near    = min([(abs(line_n-rCrt), ind)
                        for ind, (line_n, line_s, bm_kind) in enumerate(bms)])[1]
        ans = dlg_menu(app.DMENU_LIST+app.DMENU_EDITORFONT+app.DMENU_NO_FUZZY+app.DMENU_CENTERED
            , opts_key='cuda_ext.tab_bookmark'
            , cap=f(_('Tab bookmarks: {}'), len(bms)), w=1000
            , sel=near
            , its=[
                f('{}\t{}{}'
                 , line_s
                 , f('[{}] ', bm_kind-1) if bm_kind!=1 else ''
                 , 1+line_n
                 ) for line_n, line_s, bm_kind in bms
                ])
        if ans is None: return
        line_n, line_s, bm_kind    = bms[ans]
        ed.set_caret(0, line_n)
        if not (ed.get_prop(app.PROP_LINE_TOP) <= line_n <= ed.get_prop(app.PROP_LINE_BOTTOM)):
            ed.set_prop(app.PROP_LINE_TOP, str(max(0, line_n - max(5, apx.get_opt('find_indent_vert')))))
       #def dlg_bms_in_tab

    @staticmethod
    def dlg_bms_in_tabs(what='a'):
        pass;                  #return log('ok',())
        tnmd    = apx.get_opt('ui_tab_numbers', False)
        tbms    = []
        for h_tab in app.ed_handles():
            ted     = app.Editor(h_tab)
            bm_lns  = ted.bookmark(app.BOOKMARK_GET_LIST, 0)
            if not bm_lns:  continue
            tab_grp = ted.get_prop(app.PROP_INDEX_GROUP)
            tab_num = ted.get_prop(app.PROP_INDEX_TAB)
            tab_cap = ted.get_prop(app.PROP_TAB_TITLE)
            tab_id  = ted.get_prop(app.PROP_TAB_ID)
            tab_info= tab_cap \
                        if what=='a' else \
                      (f('(g{},t{}) ', 1+tab_grp, 1+tab_num) if tnmd else '') + tab_cap
            tab_id  = ted.get_prop(app.PROP_TAB_ID)
            tab_sps = ' '*ed.get_prop(app.PROP_TAB_SIZE)
            tbms   += [ (line_num                                               # line number
                        ,ted.get_text_line(line_num).replace('\t', tab_sps)     # line string
                        ,ted.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']  # kind of bm
                        ,tab_info                                               # src tab '(group:num) title'
                        ,tab_id                                                 # src tab ID
                        )   for line_num in bm_lns
                            if                 ted.bookmark(app.BOOKMARK_GET_PROP, line_num) and        # Skip hidden
                               (what=='a' or 1<ted.bookmark(app.BOOKMARK_GET_PROP, line_num)['kind']<10)
                      ]
           #for h_tab
        if not tbms:    return app.msg_status(_('No numbered bookmarks in tabs') if what=='n' else _('No bookmarks in tabs'))
        tid     = ed.get_prop(app.PROP_TAB_ID)
        rCrt    = ed.get_carets()[0][1]
        near    = min([(abs(line_n-rCrt) if tid==tab_id else 0xFFFFFF, ind)
                    for ind, (line_n, line_s, bm_kind, tab_info, tab_id) in enumerate(tbms)])[1]
        lst     = [     f('{}\t{}:{}{}'
                         , line_s
                         , tab_info
                         , f('[{}]', bm_kind-1) if bm_kind!=1 else ''
                         , 1+line_n
                         ) for line_n, line_s, bm_kind, tab_info, tab_id in tbms
                  ] \
                                if what=='a' else \
                  [     f('{}: {} {}\t{}'
                         , tab_info
                         , f('[{}] ', bm_kind-1) if bm_kind!=1 else ''
                         , 1+line_n
                         , line_s
                         ) for line_n, line_s, bm_kind, tab_info, tab_id in tbms
                  ]
        ans     = dlg_menu((app.DMENU_LIST if what=='a' else app.DMENU_LIST_ALT)+app.DMENU_EDITORFONT+app.DMENU_CENTERED
                , opts_key='cuda_ext.tabs_bookmark'
                , cap=f(_('All tabs bookmarks: {}'), len(tbms)), w=1000
                , its=lst
                , sel=near)
        if ans is None: return
        line_n, line_s, bm_kind, tab_info, tab_id    = tbms[ans]
        ted     = apx.get_tab_by_id(tab_id)
        ted.focus()
        ed.set_caret(0, line_n)
        if not (ed.get_prop(app.PROP_LINE_TOP) <= line_n <= ed.get_prop(app.PROP_LINE_BOTTOM)):
            ed.set_prop(app.PROP_LINE_TOP, str(max(0, line_n - max(5, apx.get_opt('find_indent_vert')))))
       #def dlg_bms_in_tabs

   #class Jumps_cmds

class Prgph_cmds:

    @staticmethod
    def go_prgph(what):
        """ Param 
                what    'bgn' - go to begin of current prph
                        'end' - go to end   of current prph
                        'nxt' - go to begin of next    prph
                        'prv' - go to begin of prev    prph
        """
        pass;                  #LOG and log('what={}',(what))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        cu_row  = rCrt
        
        cu_line = ed.get_text_line(cu_row)
        if ''==cu_line.strip() and what in ('bgn', 'end'):  return
        
        cu_skip = False
        if what=='end' and cu_row+1<ed.get_line_count():
            # Skip cu-prph if caret "at end" and cmd "go end"
            cu_skip = ''==ed.get_text_line(cu_row+1).strip() and \
                      cCrt==len(cu_line)
        if what=='bgn' and cu_row-1>=0:
            # Skip cu-prph if caret "at bgn" and cmd "go bgn"
            cu_skip = ''==ed.get_text_line(cu_row-1).strip() and \
                      cCrt<=len(cu_line)-len(cu_line.lstrip())
        
        if what in ('nxt', 'prv') or cu_skip:
            # Search row in other prph
            step    = 1 if what in ('nxt','end') else -1
            stop    =-1 if what in ('prv','bgn') else ed.get_line_count()
            aim     = 'skip-prph'
            for test_row in range(cu_row+step, stop, step):
                test_line   = ed.get_text_line(test_row)
                empty       = ''==test_line.strip()
                if False:pass
                elif aim=='skip-prph' and not empty:
                    pass
                elif aim=='skip-prph' and     empty:
                    aim = 'skip-free'
                elif aim=='skip-free' and     empty:
                    pass
                elif aim=='skip-free' and not empty:
                    aim = 'found'
                    break#for
               #for test_row
            if aim!='found':    return
            what    = 'bgn' if what in ('nxt', 'prv') else what
            cu_row  = test_row
            
        # Search need row in curr prph
        nd_row  = cu_row
        step    =-1 if what=='bgn' else 1
        stop    =-1 if what=='bgn' else ed.get_line_count()
        pass;                  #LOG and log('cu_row,step,stop={}',(cu_row,step,stop))
        for test_row in range(cu_row+step, stop, step):
            if ''==ed.get_text_line(test_row).strip():
                break#for
            nd_row  = test_row
           #for test_row
           
        # Set caret
        nd_text = ed.get_text_line(nd_row)
        nd_col  = len(nd_text) - len(nd_text.lstrip()) \
                    if what=='bgn' else \
                  len(nd_text)
        ed.set_caret(nd_col, nd_row)
       #def go_prgph

    @staticmethod
    def align_prgph(how):
        """ Align words in selected paragraphs
            Param 
                how     'l' - left
                        'r' - right
                        'c' - center
                        'f' - full
                        '?' - edit params
        """
        pass;                  #LOG and log('how={}',(how))
        df_mrg  = apx.get_opt('margin', 80)
        if how=='?':
            ans     = app.dlg_input_ex(3, _('Align paragraphs - options (default values)')
                , f(_('Paragraph right margin ({})'),df_mrg), str(apx.get_opt('margin_right'    , df_mrg))
                , _('Indent of first line (0)')             , str(apx.get_opt('margin_left_1'   , 0))
                , _('Indent of other lines (0)')            , str(apx.get_opt('margin_left'     , 0))
                )
            if ans:
                apx.set_opt('margin_right'  , int(ans[0]) if ans[0].isdigit() else df_mrg)
                apx.set_opt('margin_left_1' , int(ans[1]) if ans[1].isdigit() else 0)
                apx.set_opt('margin_left'   , int(ans[2]) if ans[2].isdigit() else 0)
            return
        
        if 0==apx.get_opt('margin_right', 0):
            Prgph_cmds.align_prgph('?')
            if 0==apx.get_opt('margin_right', 0):
                return
            
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))

        max_col = apx.get_opt('margin_right'    , df_mrg)
        indent  = apx.get_opt('margin_left'     , 0)
        indent1 = apx.get_opt('margin_left_1'   , 0)
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        min_row,\
        max_row = apx.minmax(rCrt, rEnd) if -1!=rEnd else (rCrt, rCrt)

        prphs   = Prgph_cmds._detect_prphs(min_row, max_row)
        pass;                  #LOG and log('prphs={}',(prphs))
        pass;                  #return
        
        for (prph_bgn_r, prphs_end_r) in reversed(prphs):
            prph_text   = ' '.join([ed.get_text_line(r)
                                    for r in range(prph_bgn_r, prphs_end_r+1)])     # join
            pass;              #LOG and log('prph_text={}',(prph_text))
            prph_text   = re.sub(r'(\s)\s+', r'\1', prph_text)                      # reduce
            pass;              #LOG and log('prph_text={}',(prph_text))
            prph_lines  = Prgph_cmds._form_prph(prph_text, how, max_col, indent, indent1)   # split and align
            pass;              #LOG and log('prph_lines={}',('\n'+'\n'.join(prph_lines)))
            ed.replace_lines(prph_bgn_r, prphs_end_r, prph_lines)
       #def align_prgph
       
    def _form_prph(text, how, max_col, indent=0, indent1=0):
        words   = [m.group() for m in re.finditer(r'\S+', text)]
#       words   = [m.group() for m in re.finditer(r'\b\S+\b', text)]
        if not words:
            return [text]
        
        width1  = max_col - indent1
        width   = max_col - indent
        pass;                  #LOG and log('width1,width={}',(width1,width))
        line_ws = []
        line_ns = []
        # Draft split
        line_n  = 0
        line    = []
        for word in words:
            if not line:
                # First word in line has any length
                line_n  = len(word)
                line    = [   word]
                continue
            if  line_n +    len(word) < (width if line_ws else width1):
                line_n += 1+len(word)
                line   += [' ', word]
            else:
                line_ws+= [line]
                line_ns+= [line_n]
                line_n  = len(word)
                line    = [   word]
           #for word
        if line:
            # tail
            line_ws+= [line]
            line_ns+= [line_n]
        pass;                  #LOG and log('line_ws={}',(line_ws))
        pass;                  #LOG and log('line_ns={}',(line_ns))
        
        widths  = [width1]      + [width]     *(len(line_ws)-1)
        shifts  = [' '*indent1] + [' '*indent]*(len(line_ws)-1)
            
        # Format lines
        if how=='l':
            return [sh+''.join(ws)
                    for    ws,sh in         zip(line_ws,shifts)]
        if how=='r':
            return [sh
                   +' '*(wd-ns)
                   +''.join(ws)
                    for ns,ws,sh,wd in zip(line_ns,line_ws,shifts,widths)]
        if how=='c':
            return [sh
                   +' '*       int((wd-ns)/2)
                   +''.join(ws)
                   +' '*(wd-ns-int((wd-ns)/2))
                    for ns,ws,sh,wd in zip(line_ns,line_ws,shifts,widths)]
        # Full
        def frm_full(ws, spaces):                           # Spaces needs to append 
            if not spaces:      return ws
            insides = int((len(ws) - 1 )/2)                 # Count of inside space-items: ['w',' ','w',' ','w']
            if not insides:     return ws + [' '*spaces]
            pass;              #LOG and log('ws={}',(ws))
            quant   = max(int(spaces / insides), 1)         # Size  of first  appending q-block
            quants  = min(int(spaces / quant), insides) \
                        if quant else 0                     # Count of first  appending q-block
            extra   =     spaces - quant*quants             # Count of second appending 1-block
            pass;              #LOG and log('(spaces,insides),(quant,quants),extra={}',((spaces,insides),(quant,quants),extra))
            if quants:
                quant_s = ' '*quant
                gap     = max(1, int(insides/quants))
                pass;          #LOG and log('gap={}',(gap))
                for q_i in range(quants):
                    ins = q_i * gap
                    ws[1+2*ins] += quant_s
            if extra:
                gap     = max(1, int(insides/extra))
                pass;          #LOG and log('gap={}',(gap))
                for q_i in range(extra):
                    ins = q_i * gap
                    ws[-2-2*ins] += ' '
            pass;              #LOG and log('ws={}',(ws))
            return ws
           #def frm_full
        
        return     [sh+''.join(frm_full(ws, wd-ns))
                    for ns,ws,sh,wd in zip(line_ns[:-1],line_ws[:-1],shifts[:-1],widths[:-1])] \
                 + [shifts[-1]+''.join(line_ws[-1])]        # Last line has with left format
       #def _form_prph
    
    def _detect_prphs(min_row, max_row):
        pass;                  #LOG and log('min_row, max_row={}',(min_row, max_row))
        pass;                  #return [(min_row, max_row)]
        if min_row>max_row:
            return []
        # Expand/reduce to whole prphs
        def find_row(start, what):
            rsp     = start
            step    = 1 if what=='bot-prph' else -1
            stop    =-1 if what=='top-prph' else ed.get_line_count()
            pass;              #LOG and log('start, stop, step={}',(start, stop, step))
            for row in range(start, stop, step):
                if ''==ed.get_text_line(row).strip():
                    return rsp
                rsp = row
            return rsp
           #def find_row
           
        min_row = find_row(min_row, 'top-prph') #if ''!=ed.get_text_line(min_row).strip() else min_row
        max_row = find_row(max_row, 'bot-prph') #if ''!=ed.get_text_line(max_row).strip() else max_row
        pass;                  #LOG and log('min_row, max_row={}',(min_row, max_row))
        prphs   = []
        top,bot = None,None
        inside  = False
        for row in range(min_row, max_row+1):
            empty   = ''==ed.get_text_line(row).strip()
            if False:pass
            elif not inside and     empty:
                pass
            elif not inside and not empty:
                top     = row
                bot     = row
                inside  = True
            elif     inside and not empty:
                bot     = row
            elif     inside and     empty:
                prphs  += [(top, bot)]
                inside  = False
           #for row
        if inside:
            prphs      += [(top, bot)]
        return prphs
       #def _detect_prphs
        
   #class Prgph_cmds

#############################################################
class Nav_cmds:
    @staticmethod
    def on_console_nav(ed_self, text):
        pass;                      #LOG and log('text={}',text)
        match   = re.match('.*File "([^"]+)", line (\d+)', text)    ##?? variants?
        if match is None:
            return
        op_file =     match.group(1)
        op_line = int(match.group(2))-1
        pass;                      #LOG and log('op_line, op_file={}',(op_line, op_file))
        if not os.path.exists(op_file):
            return app.msg_status(NO_FILE_FOR_OPEN.format(op_file))
        op_ed   = _file_open(op_file)
        op_ed.focus()
        op_ed.set_caret(0, op_line)
        op_ed.set_prop(app.PROP_LINE_TOP, max(0, op_line-5)) #scroll to caret
       #def on_console_nav

    @staticmethod
    def _open_file_near(where='right'):
        cur_path= _get_filename(ed)
        init_dir= os.path.dirname(cur_path) if cur_path else ''
        fls     = app.dlg_file(True, '*', init_dir, '')   # '*' - multi-select
        if not fls: return
        fls     = [fls] if isinstance(fls, str) else fls

        group   = ed.get_prop(app.PROP_INDEX_GROUP)
        tab_pos = ed.get_prop(app.PROP_INDEX_TAB)
        if False:pass
        elif where=='right':
            for fl in reversed(fls):
                app.file_open(fl, group)
                ed.set_prop(app.PROP_INDEX_TAB, str(1+tab_pos))
        elif where=='left':
            for fl in fls:
                app.file_open(fl, group)
                ed.set_prop(app.PROP_INDEX_TAB, str(tab_pos))
                tab_pos +=1
       #def open_file_near
    
    @staticmethod
    def nav_by_console_err():
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        cons_out= '\n'.join(app.app_log(app.LOG_CONSOLE_GET_MEMO_LINES, ''))
        if 'The above exception was the direct cause' in cons_out:
            cons_out= cons_out[:cons_out.find('The above exception was the direct cause')]
           #app.app_log(app.LOG_CONSOLE_CLEAR)
            print(cons_out)
        fn      = _get_filename(ed)
        if not fn:      return app.msg_status(_('Only for saved file'))
        fn_ln_re= f('File "{}", line ', fn).replace('\\','\\\\')+'(\d+)'
        pass;                      #LOG and log('fn_ln_re={}',fn_ln_re)
        mtchs   = list(re.finditer(fn_ln_re, cons_out, re.I))
        if not mtchs:   return app.msg_status(_('In output no errors or no current file: ')+fn)
        mtch    = mtchs[-1]
        row     = int(mtch.group(1))-1
        pass;                      #LOG and log('row={}',row)
        ed.set_caret(0, row)
       #def nav_by_console_err

    @staticmethod
    def open_selected():
        pass;                      #LOG and log('ok',)
        bs_dirs     = [os.path.dirname(_get_filename(ed))
                    ,  os.environ.get('TEMP', '')
                    ]
        crts        = ed.get_carets()
        if len(crts)!=1: return
        (cCrt, rCrt
        ,cEnd, rEnd)= crts[0]
        pointed = ed.get_text_sel()
        if not pointed:
            # Empty selection, will use word/term
            line    = ed.get_text_line(rCrt)
            (pointed
            ,where) = get_word_or_quoted(line, cCrt)
        pass;                      #LOG and log('pointed={}',pointed)
        if not pointed: return
        op_ed   = None
        for bs_dir in bs_dirs:
            op_file     = os.path.join(bs_dir, pointed)
            op_row      = -1
            if not os.path.isfile(op_file) and \
               '(' in op_file:                                      #)
                    # Try to split in 'path(row'                    #)
                    mtch= re.search(r'(.*)\((\d+)', op_file)
                    if mtch:
                        pointed_,op_row = mtch.groups()
                        op_row          = int(op_row)
                        op_file         = os.path.join(bs_dir, pointed_)
            if os.path.isfile(op_file):
                op_ed   = _file_open(op_file)
                op_ed.focus()
                if op_row!=-1:
                    op_ed.set_caret(0, op_row)
                break#for
        if not op_ed:
            return app.msg_status(NO_FILE_FOR_OPEN.format(pointed))
       #def open_selected
   #class Nav_cmds


#############################################################
class Insert_cmds:
    @staticmethod
    def add_indented_line_above():  ##!!
        ed.cmd(cmds.cCommand_KeyUp)
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_above
    @staticmethod
    def add_indented_line_below():  ##!!
        ed.cmd(cmds.cCommand_KeyEnd)
        ed.cmd(cmds.cCommand_KeyEnter)
       #def add_indented_line_below

    @staticmethod
    def indent_and_surround(str_bfr, str_aft):
        """ Algo by Alexey Torgashin  """

        def str_get_indent(s):
        	n = 0
        	while (n<len(s)) and (s[n] in [' ', '\t']):
        		n += 1
        	return s[:n]
    
        def str_indented(s, indent_add):
            if s:
                s = indent_add + s
            return s
  
        n1, n2 = ed.get_sel_lines()
        if n1<0:
            app.msg_status(_('No text selected'))
            return
            
        lines = [ed.get_text_line(i) for i in range(n1, n2+1)]
        if not lines: return
        
        indent = str_get_indent(lines[0])
        tab_spaces = ed.get_prop(app.PROP_TAB_SPACES)
        tab_size = ed.get_prop(app.PROP_TAB_SIZE)
        eol = '\n'
        indent_add = ' '*tab_size if tab_spaces else '\t'
        
        lines = [str_indented(s, indent_add) for s in lines]
        lines = [indent + str_bfr] + lines + [indent + str_aft]
        newtext = eol.join(lines) + eol
        
        ed.set_caret(0, n1)
        ed.replace_lines(n1, n2, lines)
        app.msg_status(_(f'Indented {n2-n1+1} lines'))
       #def indent_and_surround


    @staticmethod
    def paste_to_1st_col():
        ''' Paste from clipboard without replacement caret/selection
                but only insert before current line
        '''
        pass;                      #LOG and log('')
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip:    return
        clip    = clip.replace('\r\n', '\n').replace('\r', '\n')
        if not (clip[-1] in '\r\n'):
            clip= clip + '\n'
        rnews   = clip.count('\n')
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        (cCrt, rCrt, cEnd, rEnd)    = crts[0]
        r4ins   = min(rCrt, rCrt if -1==rEnd else rEnd)
        ed.insert(0, r4ins, clip)
        rCrtN   = rCrt+ rnews
        rEndN   = rEnd+(rnews if -1!=rEnd else 0)
        pass;                      #LOG and log('(rCrtN, rEndN)={}',(rCrtN, rEndN))
        ed.set_caret(cCrt, rCrtN
                    ,cEnd, rEndN)
        pass;                   return  ##??
       #def paste_to_1st_col

    @staticmethod
    def paste_with_indent(where='above'): ##!!
        ''' Paste above/below with fitting indent of clip to indent of active line
            Param
                where   'above' Insert between this and prev line
                        'below' Insert between this and next line
#                       'lazar' Insert between this and prev line 
#                                   if caret before text else
#                               normal insert 
        '''
        clip    = app.app_proc(app.PROC_GET_CLIP, '')
        pass;                      #LOG and log('clip={}',repr(clip))
        if not clip:        return app.msg_status(_('Empty clip'))
        if not clip.strip():return app.msg_status(_('No text in clip'))
        crts    = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))

        END_SIGNS = ['begin', '{', ':', 'then']   # }

        use_tab = not ed.get_prop(app.PROP_TAB_SPACES)  # apx.get_opt('tab_spaces')
        sps_tab = ' '*ed.get_prop(app.PROP_TAB_SIZE)    # apx.get_opt('tab_size')
        pass;                      #LOG and log('use_tab,sps_tab={}',(use_tab,sps_tab))

        (cCrt, rCrt, cEnd, rEnd) = crts[0]
        if cEnd!=-1:    return app.msg_status(_('Command works only if no selection'))
        r4ins   = rCrt  # min(rCrt, rCrt if -1==rEnd else rEnd)
        ln_tx   = ed.get_text_line(r4ins).rstrip()
#       if where=='lazar':
#           return
            
        if where=='below' and \
            any(map(lambda sign:ln_tx.lower().endswith(sign), END_SIGNS)):
            # Extra indent
            ln_tx = ('\t' if use_tab else sps_tab) + ln_tx
        
        # Fit clip
        lns_cl  = clip.splitlines()
        def replaces_spaces_atstart(s, what_s, with_s):
            ind_tx  = len(s) - len(s.lstrip())
            return s[:ind_tx].replace(what_s, with_s) + s[ind_tx:]
        if     use_tab and clip[0]==' ':
            # Replace spaces to tab in begining of each clip lines
            lns_cl  = [replaces_spaces_atstart(cl_ln, sps_tab, '\t')
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('sp->tb lns_cl={}',(lns_cl))
        if not use_tab and clip[0]=='\t':
            # Replace tab to spaces in begining of each clip lines
            lns_cl  = [replaces_spaces_atstart(cl_ln, '\t', sps_tab)
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('tb->sp lns_cl={}',(lns_cl))
        
        ind_ln  =      len(ln_tx) - len(ln_tx.lstrip())
        ind_cl  = min([len(cl_ln) - len(cl_ln.lstrip())
                       for cl_ln in lns_cl])
        pass;                      #LOG and log('ind_ln, ind_cl={}',(ind_ln, ind_cl))
        if False:pass
        elif ind_cl > ind_ln:
            # Cut clip lines
            lns_cl  = [cl_ln[  ind_cl - ind_ln:]
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('cut lns_cl={}',(lns_cl))
        elif ind_ln > ind_cl:
            # Add to clip lines
            apnd    = ln_tx[0]*(ind_ln - ind_cl)
            lns_cl  = [apnd+cl_ln
                       for cl_ln in lns_cl]
            pass;                  #LOG and log('add lns_cl={}',(lns_cl))
        clip    = '\n'.join(lns_cl)
        clip    = clip+'\n' if clip[-1] not in '\n\r' else clip
        
        # Insert
        pass;                      #LOG and log('ln_tx={}',repr(ln_tx))
        pass;                      #LOG and log('clip={}',repr(clip))
        if where=='above':
            ed.insert(0, r4ins,   clip)
        else:
            ed.insert(0, r4ins+1, clip)
       #def paste_with_indent

    @staticmethod
    def paste_trimmed():
        clip = app.app_proc(app.PROC_GET_CLIP, '')
        if not clip.strip():
            return app.msg_status(_('Clipboard has no text'))
        clip = '\n'.join(l.strip() for l in clip.splitlines())
        
        crts = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
        
        x1, y1, x2, y2 = crts[0]
        if y2>=0:
            if (y1, x1)>(y2, x2):
                x1, y1, x2, y2 = x2, y2, x1, y1
            ed.delete(x1, y1, x2, y2)
            clip += ('\n' if y1!=y2 and x2==0 else '') # To avoid bug in ed.insert
        x, y = ed.insert(x1, y1, clip)
        ed.set_caret(x, y)

        app.msg_status(_('Pasted trimmed text'))
       #def paste_trimmed

    @staticmethod
    def trim_sel(mode):
        crts = ed.get_carets()
        if len(crts)>1:
            return app.msg_status(ONLY_SINGLE_CRT.format(_('Command')))
    
        x1, y1, x2, y2 = crts[0]
        if y2<0:
            return app.msg_status(_('Need selection'))
        
        if (y1, x1)>(y2, x2):
            x1, y1, x2, y2 = x2, y2, x1, y1
        
        text = ed.get_text_substr(x1, y1, x2, y2)
        trimmer = lambda s:(s.lstrip()   if mode=='left'  else
                            s.rstrip()   if mode=='right' else
                            s.strip()   #if mode=='all'
                           )
        text2 = '\n'.join(trimmer(l) for l in text.splitlines())
        if text==text2:
            return app.msg_status(_('Text already trimmed'))
        text2 += ('\n' if x2==0 else '')    # To avoid bug in ed.replace
        
        x3, y3 = ed.replace(x1, y1, x2, y2, text2)
        ed.set_caret(x1, y1, x3, y3)
        app.msg_status(_('Text trimmed'))
       #def trim_sel

    @staticmethod
    def fill_by_str():
        crts    = ed.get_carets()
        if all(-1==cEnd for cCrt, rCrt, cEnd, rEnd in crts):    return
        str2fill    = app.dlg_input(_('Enter string to fill selection'), '')
        if not str2fill:    return
        cnt = 0
        for cCrt, rCrt, cEnd, rEnd in crts:
            if -1  ==cEnd:    continue
            if rCrt!=rEnd:    continue
            ((rSelB, cSelB)
            ,(rSelE, cSelE))= apx.minmax((rCrt, cCrt), (rEnd, cEnd))
            trg_len = cSelE - cSelB
            trg_str = str2fill * (1  + int(trg_len/len(str2fill)))
            trg_str = trg_str[:trg_len]
            ed.replace(cSelB, rSelB, cSelE, rSelE, trg_str)
            cnt += 1
           #for
        if cnt>0:
            app.msg_status(_('Changed %d selection(s)')%cnt)
        else:
            app.msg_status(_('Need single-line selection(s)'))
        pass;                   LOG and log('ok',())
       #def fill_by_str

    @staticmethod
    def copy_unicode_char_name():
        ch_xy   = ed.get_carets()[0][:2]
        ch_line = ed.get_text_line(ch_xy[1])
        ch      = ch_line[ch_xy[0]:ch_xy[0]+1]
        if not ch: return 
        ch_um   = unicodedata.name(ch)
        app.app_proc(app.PROC_SET_CLIP, ch_um)
        app.msg_status(f('Copy "{}"', ch_um))
       #def copy_unicode_char_name

    @staticmethod
    def insert_char_by_hex():
        hexcode = app.dlg_input(_('Character hex code, optional 0x prefix:'), '')
        if not hexcode:
            return
        if not re.search(r'(0x)?[\da-f]{1,4}', hexcode):
            app.msg_status(_('Not valid hex code: ') + hexcode)
            return

        hexcode = hexcode.upper()
        hexcode = hexcode[2:]   if hexcode.startswith('0X') else hexcode
        while len(hexcode)<4:
            hexcode = '0'+hexcode #to show nice status

        try:
            text = chr(int(hexcode, 16))
        except:
            app.msg_status(_('Not valid hex code: ') + hexcode)
            return

        #this supports multi-carets on insert
        ed.cmd(cmds.cCommand_TextInsert, text)
        app.msg_status(_('Character inserted: U+') + hexcode)
       #def insert_char_by_hex
    
   #class Insert_cmds
    
class Command:
#   def __init__(self):
       #def __init__
        

    def layouts(self, what):
        lts     = get_hist('splitters_layouts', {}) # {nm:{side:pos, bott:pos, spl1:pos, spl2:pos, spl3:pos, spl4:pos, spl5:pos}}
        pass;                  #log("lts={}",pfrm100(lts))

        if False:pass
        elif what=='save':
            nm      = ''
            while True:
                nm  = app.dlg_input(_('Name to save splitters layout'), f'#{1+len(lts)}')
                if not nm: return 
                if nm not in lts:       break#while
                qu  = f(_('Layout with name "{nm}" already exists. Replace?'), nm=nm)
#               qu  = _(f'Layout with name "{nm}" already exists. Replace?')
                ans = app.msg_box(qu, app.MB_YESNOCANCEL+app.MB_ICONQUESTION)
                if ans==app.ID_CANCEL:  return 
                if ans==app.ID_YES:     break#while
            # (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_SPLITTER_GET, id_splt)
            sid_vis  = lambda sid: app.app_proc(app.PROC_SPLITTER_GET, sid)[1]
            sid_pos  = lambda sid: app.app_proc(app.PROC_SPLITTER_GET, sid)[2]
            lt  = dict( side=sid_pos(app.SPLITTER_SIDE)     if sid_vis(app.SPLITTER_SIDE)   else 0,
                        bott=sid_pos(app.SPLITTER_BOTTOM)   if sid_vis(app.SPLITTER_BOTTOM) else 0,
                        spl1=sid_pos(app.SPLITTER_G1)       if sid_vis(app.SPLITTER_G1)     else 0,
                        spl2=sid_pos(app.SPLITTER_G2)       if sid_vis(app.SPLITTER_G2)     else 0,
                        spl3=sid_pos(app.SPLITTER_G3)       if sid_vis(app.SPLITTER_G3)     else 0,
                        spl4=sid_pos(app.SPLITTER_G4)       if sid_vis(app.SPLITTER_G4)     else 0,
                        spl5=sid_pos(app.SPLITTER_G5)       if sid_vis(app.SPLITTER_G5)     else 0,
                        grps=app.app_proc(app.PROC_GET_GROUPING, ''),
                )
            lts[nm] = lt
            set_hist('splitters_layouts', lts)
        
        elif what in ('remove', 'restore'):
            if not lts: return app.msg_status(_('No saved layout'))
            nm      = ''
            lt      = None
            if 1==len(lts) and what=='restore':
                nm  = list(lts)[0]
                lt  = lts[nm]
            else:
                cap     = _('Remove layout?') if what=='remove' else _('Restore layout?')
                ans     = app.dlg_menu(app.DMENU_LIST, [nm for nm in lts], caption=cap, opts_key='cuda_ext.layouts')
                if ans is None: return 
                nm      = list(lts.keys())[ans]
                if what=='remove':
                    del lts[nm]
                    set_hist('splitters_layouts', lts)
                    return 
                lt  = lts[nm]
            # Restore
            pass;              #log("lt={}",pfrm100(lt))
            if  app.app_proc(app.PROC_GET_GROUPING, '')!=lt['grps']:
                app.app_proc(app.PROC_SET_GROUPING,      lt['grps'])
            sid_pos  = lambda sid, pos: app.app_proc(app.PROC_SPLITTER_SET, (sid, pos))
            if lt['side']:
                app.app_proc(app.PROC_SHOW_SIDEPANEL_SET, True)
                sid_pos(app.SPLITTER_SIDE   , lt['side'])
            if lt['bott']:
                app.app_proc(app.PROC_SHOW_BOTTOMPANEL_SET, True)
                sid_pos(app.SPLITTER_BOTTOM , lt['bott'])
            for g in range(1,6):
                if lt[f'spl{g}']:
                    app.app_proc(app.PROC_SPLITTER_SET, (eval(f'app.SPLITTER_G{g}'), lt[f'spl{g}']))
            app.msg_status(_('Restored layout: ')+nm)
#           app.msg_status(_(f'Restored layout: {nm}'))
       #def layouts


    def _move_splitter(self, what, factor):
        ''' Move one of splitters
            Params:
                what    Which splitter and changing width or height 
                            'into'          - into tab, direction as is
                            'left'          - tree
                            'bott'          - console/output/...
                            'main'          - top-left group, 
                                                width if has right neighbor
                                                else height
                            'curr'          - active group, 
                                                self     width  if has right  neighbor
                                                neighbor width  if has left   neighbor
                                                self     height if has bottom neighbor
                                                neighbor height if has upper  neighbor
                factor  Multiplier for relation pos of splitter.
                            NewPos  = int(factor * OldPos)
        '''
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(NEED_UPDATE)
        pass;                  #LOG and log('what, factor={}',(what, factor))
        id_splt     = ''
        pos_old     = 0
        prn_size    = 0
        if False:pass
        elif what=='into':  # In tab 
            return
        
        elif what=='left':  # Tree
            id_splt     = 'L'
        elif what=='bott':  # Bottom
            id_splt     = 'B'
        
        else:               # Groups
            # [('G'+str(i), list(zip(('|','V','P','F'), app.app_proc(app.PROC_GET_SPLIT, 'G'+str(i))))) for i in (1,2,3)]
            # 2HORZ     0 G1 1
            # 2VERT     0
            #           G1
            #           1
            # 3HORZ     0 G1 1 G2 2
            # 3VERT     0
            #           G1
            #           1
            #           G2
            #           2
            # 1P2VERT   0 G3 1 
            #                G2 
            #                2 
            # 1P2HORZ   0
            #           G3 
            #           1 G2 2 
            # 4HORZ     0 G1 1 G2 2 G3 3
            # 4VERT     0
            #           G1
            #           1
            #           G2
            #           2
            #           G3
            #           3
            # 4GRID     0 G1 1
            #           G3
            #           2 G2 3
            # 6GRID     0 G1 1 G2 2
            #           G3
            #           3 G1 4 G2 5
            grouping    = app.app_proc(app.PROC_GET_GROUPING, '')
            cur_grp     = ed.get_prop(app.PROP_INDEX_GROUP)
            if False:pass
            elif grouping==app.GROUPS_ONE:
                return      # No splitter

            elif (what=='main'
#           and   grouping!=app.GROUPS_3PLUS):      id_splt = 'G1'
            and   grouping!=app.GROUPS_1P2VERT
            and   grouping!=app.GROUPS_1P2HORZ):    id_splt = 'G1'
            
            elif (what=='main'
#           and   grouping==app.GROUPS_3PLUS):      id_splt = 'G3'
            and   grouping==app.GROUPS_1P2VERT):    id_splt = 'G3'

            elif (what=='main'
            and   grouping==app.GROUPS_1P2HORZ):    id_splt = 'G3'

            #     what=='curr'
            elif cur_grp==0:
                if False:pass
                elif grouping==app.GROUPS_2HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_2VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_3HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_3VERT:    id_splt = 'G1'  # h-self
#               elif grouping==app.GROUPS_3PLUS:    id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_1P2VERT:  id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_1P2HORZ:  id_splt = 'G3'  # h-self
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G1'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt = 'G1'  # w-self
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G1'  # w-self

            elif cur_grp==1:
                if False:pass
                elif grouping==app.GROUPS_2HORZ:    id_splt ='-G1'  # w-left
                elif grouping==app.GROUPS_2VERT:    id_splt ='-G1'  # h-top
                elif grouping==app.GROUPS_3HORZ:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_3VERT:    id_splt = 'G2'  # h-self
#               elif grouping==app.GROUPS_3PLUS:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_1P2VERT:  id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_1P2HORZ:  id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G2'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt ='-G1'  # w-left
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G2'  # w-self

            elif cur_grp==2:
                if False:pass
                elif grouping==app.GROUPS_3HORZ:    id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_3VERT:    id_splt ='-G2'  # h-top
#               elif grouping==app.GROUPS_3PLUS:    id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_1P2VERT:  id_splt ='-G2'  # h-top
                elif grouping==app.GROUPS_1P2HORZ:  id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_4HORZ:    id_splt = 'G3'  # w-self
                elif grouping==app.GROUPS_4VERT:    id_splt = 'G3'  # h-self
                elif grouping==app.GROUPS_4GRID:    id_splt = 'G2'  # w-self
                elif grouping==app.GROUPS_6GRID:    id_splt ='-G2'  # w-left

            elif cur_grp==3:
                if False:pass
                elif grouping==app.GROUPS_4HORZ:    id_splt ='-G3'  # w-left
                elif grouping==app.GROUPS_4VERT:    id_splt ='-G3'  # h-top
                elif grouping==app.GROUPS_4GRID:    id_splt ='-G2'  # w-left
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G1'  # w-self

            elif cur_grp==4:
                if False:pass
                elif grouping==app.GROUPS_6GRID:    id_splt = 'G2'  # w-self

            elif cur_grp==5:
                if False:pass
                elif grouping==app.GROUPS_6GRID:    id_splt ='-G2'  # w-left

            else:
                return
        if id_splt[0]=='-':
            id_splt = id_splt[1:]
            factor  = 2 - factor
        id_splt = {'L': app.SPLITTER_SIDE
                  ,'B': app.SPLITTER_BOTTOM
                  ,'G1':app.SPLITTER_G1
                  ,'G2':app.SPLITTER_G2
                  ,'G3':app.SPLITTER_G3
                  }[id_splt]

        (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_SPLITTER_GET, id_splt)
        pass;                  #LOG and log('vh, shown, pos_old, prn_size={}',(vh, shown, pos_old, prn_size))
#       (vh, shown, pos_old, prn_size)  = app.app_proc(app.PROC_GET_SPLIT, id_splt)
        pass;                  #LOG and log('id_splt, vh, shown, pos_old, prn_size={}',(id_splt, vh, shown, pos_old, prn_size))
        if not shown:           return
        pos_new     = int(factor * pos_old)
        pass;                  #LOG and log('pos_new={}',(pos_new))
        pos_new     = max(100, min(prn_size-100, pos_new))
        pass;                  #LOG and log('pos_new={}',(pos_new))
        if pos_new==pos_old:    return
        pass;                  #LOG and log('id_splt, pos_new={}',(id_splt, pos_new))
        app.app_proc(app.PROC_SPLITTER_SET, (id_splt, pos_new))
#       app.app_proc(app.PROC_SET_SPLIT, '{};{}'.format(id_splt, pos_new))
       #def _move_splitter


    def rename_file(self):
        old_path= _get_filename(ed)
        if not old_path:
            return ed.cmd(cmds.cmd_FileSaveAs)
        old_fn  = os.path.basename(old_path)
        old_stem= old_fn[: old_fn.rindex('.')]  if '.' in old_fn else old_fn
        old_ext = old_fn[1+old_fn.rindex('.'):] if '.' in old_fn else ''

        def do_ok(ag, aid, data=''):
            new_stem    = ag.val('stem')
            new_ext     = ag.val('sext')
            new_path    = os.path.dirname(old_path) + os.sep + new_stem + ('.'+new_ext if new_ext else '')
            pass;              #log("new_path,old_path,os.path.isdir(new_path)={}",(new_path,old_path,os.path.isdir(new_path)))
            if new_path==old_path:
               return ag.hide('')
            if os.path.isdir(new_path):
                app.msg_box(f(_('There is directory with name:\n{}\n\nChoose another name.'), new_path), app.MB_OK)
                return []
            if os.path.isfile(new_path):
                if app.ID_YES!=app.msg_box(f(_('File\n{}\nalready exists.\n\nReplace?'), new_path), app.MB_YESNO):
                    return []
            return ag.hide(new_path)
           #def do_ok
        
        DLG_W,\
        DLG_H   = (400, 80)
        ag      = DlgAg(
            form    =dict(cap=_('Rename file')
                         ,w=5+DLG_W+5   , w_min=5+DLG_W-200+5   # Start w isnot min
                         ,h=5+DLG_H+5   , h_max=5+DLG_H+5       # Fixed h
                         ,frame='resize'
                         )
        ,   ctrls   =[0
            ,('ste_',d(tp='labl',y  =5      ,x=5        ,au=True,cap=_('Enter n&ew file name:') )) # &e
            ,('stem',d(tp='edit',y  =5+18   ,x=5        ,w=DLG_W-100+10         ,a='r>'         )) # 
            ,('sex_',d(tp='labl',tid='stem' ,x=-5-80-12 ,au=True,cap='>&.'      ,a='>>'         )) # .
            ,('sext',d(tp='edit',tid='stem' ,x=-5-80    ,w=80                   ,a='>>'         ))
            ,('!'   ,d(tp='bttn',y  =-33    ,x=-5-170   ,w=80   ,cap=_('OK')    ,a='>>' ,on=do_ok   ,def_bt='1' )) #
            ,('-'   ,d(tp='bttn',y  =-33    ,x=-5-80    ,w=80   ,cap=_('Cancel'),a='>>' ,on=CB_HIDE             ))
                    ][1:]
        ,   fid     ='stem'
        ,   vals    = d(stem=old_stem, sext=old_ext)
        ,   opts    ={  'negative_coords_reflect':True
#                   ,   'gen_repro_to_file':'repro_dlg_rename_file.py'
                    }
        )
        rsp,vals    = ag.show()
        if rsp in (None, '-'): return
        new_path    = rsp

        group       = ed.get_prop(app.PROP_INDEX_GROUP)
        tab_pos     = ed.get_prop(app.PROP_INDEX_TAB)
        crt         = ed.get_carets()[0]

        if ed.get_prop(app.PROP_MODIFIED):
            ans     = app.msg_box(_('Text modified.\nSave it?\n\nYes - Save and rename\nNo - Lost and rename\nCancel - Nothing'), app.MB_YESNOCANCEL)
            if ans==app.ID_CANCEL:  return
            if ans==app.ID_NO:
                ed.set_prop(app.PROP_MODIFIED, '0')     #? Changes lose!
            if ans==app.ID_YES:
                ed.save()

        ed.cmd(cmds.cmd_FileClose)

        os.replace(old_path, new_path)
        for ext in ('.cuda-pic', '.cuda-colortext'):
            if os.path.isfile(old_path+ext):
                os.replace(old_path+ext, new_path+ext)

        app.file_open(new_path, group)
        ed.set_prop(app.PROP_INDEX_TAB, str(tab_pos))
        ed.set_caret(*crt)
       #def rename_file

    def reopen_as(self, how):
        fn  = _get_filename(ed)
        if not fn or ed.get_prop(app.PROP_MODIFIED):
            return app.msg_status(_('Save file first'))
        
        if app.app_api_version()<'1.0.340':
            return app.msg_status(NEED_UPDATE)
        kind_f  = ed.get_prop(app.PROP_KIND)
        kind_v  = ed.get_prop(app.PROP_V_MODE)
        if how=='text' and kind_f=='text'                          \
        or how=='hex'  and kind_f=='bin'  and kind_v==app.VMODE_HEX:
            return app.msg_status(_('No need to do anything'))
            
        if how=='text':
            ed.set_prop(app.PROP_V_MODE, app.VMODE_NONE)
            app.msg_status(_('Reopened in text editor'))
        elif how=='hex':
            ed.set_prop(app.PROP_V_MODE, app.VMODE_HEX)
            app.msg_status(_('Reopened in hex viewer'))
       #def reopen_as

    def new_file_save_as_near_cur(self):
        cur_fn  = _get_filename(ed)
        if not cur_fn:  return app.msg_status(_('Warning: the command needs a named tab.'))
        cur_dir = os.path.dirname(cur_fn)
        new_fn  = app.dlg_file(False, '', cur_dir, '')
        if not new_fn:  return
        app.file_open('')
        ed.save(new_fn)
       #def new_file_save_as_near_cur

    def open_recent(self):
        home_s      = os.path.expanduser('~')
        def full_fn(fn):
            if fn.startswith('~'+os.sep):
                fn = fn.replace('~'+os.sep, home_s+os.sep, 1)
            return fn

        hist_fs     = app.app_path(app.APP_FILE_RECENTS).splitlines() # not split('\n') because Cud's APP_FILE_RECENTS has bug on Windows
        hist_fts    = [(f, os.path.getmtime(full_fn(f)))
                        for f in hist_fs if os.path.isfile(full_fn(f))]
        
        sort_as     = get_hist([           'open-recent','sort_as'],
                      apx.get_opt('cuda_ext.open-recent.sort_as'    , 't'))
        show_as     = get_hist([           'open-recent','show_as'],
                      apx.get_opt('cuda_ext.open-recent.show_as'    , 'n'))
        w           = get_hist([           'open-recent','w']       , 800)
        h           = get_hist([           'open-recent','w']       , 600)
        while True:
            hist_fts    = sorted(hist_fts
                                , key=lambda ft:(ft[1]          if sort_as=='t' else
                                                 ft[0].upper()  if show_as=='p' else
                                                 os.path.basename(ft[0]).upper()
                                                )
                                , reverse=(sort_as=='t'))
            ans         = dlg_menu(app.DMENU_LIST+app.DMENU_EDITORFONT+app.DMENU_NO_FUZZY, opts_key='cuda_ext.recents'
                        , clip=app.CLIP_MIDDLE, w=w, h=h
                        , cap=f(_('Recent files: {}'), len(hist_fts))
                        , its=[
                            (fn if show_as=='p' else
                             f('{} ({})', os.path.basename(fn), os.path.dirname(fn)))
                            + '\t'
                            + time.strftime("%Y/%b/%d %H:%M", time.gmtime(tm))
                            for fn,tm in hist_fts
                          ]
                          +[_('<Show "name (path)">')   if show_as=='p' else
                            _('<Show "path/name">')]
                          +[_('<Sort by path>')         if sort_as=='t' and show_as=='p' else
                            _('<Sort by name>')         if sort_as=='t' and show_as=='n' else
                            _('<Sort by time>')]
                                      )
            if ans is None: return
            if ans==(0+len(hist_fts)):
                show_as     = 'p' if show_as=='n' else 'n'
                set_hist(['open-recent','show_as'], show_as)
                continue #while
            if ans==(1+len(hist_fts)):
                sort_as     = 'p' if sort_as=='t' else 't'
                set_hist(['open-recent','sort_as'], sort_as)
                continue #while

            fn = hist_fts[ans][0]
            if fn.startswith('~'+os.sep):
                fn = fn.replace('~'+os.sep, home_s+os.sep, 1)
            return app.file_open(fn)
#           break#while
           #while
       #def open_recent

    def open_all_with_subdir(self):
        src_dir = app.dlg_dir(os.path.dirname(_get_filename(ed)))
        if not src_dir: return
        masks   = app.dlg_input(_('Mask(s) for filename ("*" - all files; "*.txt *.bat" - two masks)'), '*')
        if not masks: return
        masks   = re.sub(r'\s\s+', ' ', masks)
        masks   = masks.split(' ')
        files   = []
        dirs    = set()
        for dirpath, dirnames, filenames in os.walk(src_dir):
            dir_fs  = [dirpath+os.sep+fn for fn in filenames
                        if any(map(lambda mask:fnmatch(fn, mask), masks))]
#           dir_fs  = [dirpath+os.sep+fn for fn in filenames
#                       if fnmatch(fn, mask)]
            if dir_fs:
                files  += dir_fs
                dirs.add(dirpath)

        pass;                  #LOG and log('dirs={}',(dirs))
        if app.ID_OK!=app.msg_box(
            f(_('Open {} file(s) from {} folder(s)?{}'), len(files), len(dirs), '\n   '+'\n   '.join(
                files
                    if len(files) < 5*2+2 else
                files[:5] + ['...'] + files[-5:]
            ))
            , app.MB_OKCANCEL ):   return
            
        for (i, fn) in enumerate(files):
            if i%5 == 0:
                app.app_idle()
            app.app_proc(app.PROC_PROGRESSBAR, i * 100 // len(files))
            app.file_open(fn, options='/passive /nonear /nontext-view-binary')
        app.app_proc(app.PROC_PROGRESSBAR, -1)
       #def open_all_with_subdir
    
    def open_with_defapp(self):
        fn = _get_filename(ed)
        if not fn:
            return app.msg_status(_('No file to open.'))
        if ed.get_prop(app.PROP_MODIFIED) and \
            app.msg_box(  _('Text is modified!'
                          '\nCommand will use file content from disk.'
                        '\n\nContinue?')
                           ,app.MB_YESNO+app.MB_ICONQUESTION
                           )!=app.ID_YES:   return
        try:
            suffix = app.app_proc(app.PROC_GET_OS_SUFFIX, '')
            if suffix=='':
                #Windows
                os.startfile(fn)
            elif suffix=='__mac':
                #macOS
                os.system('open "'+fn+'"')
            elif suffix=='__haiku':
                #Haiku
                app.msg_status('TODO: implement "Open in default app" for Haiku')
            else:
                #other Unixes
                os.system('xdg-open "'+fn+'"')
        except Exception as ex:
            pass;               log(traceback.format_exc())
            return app.msg_status(_('Error: ')+ex)
       #def open_with_defapp
    
    def save_tabs_to_file(self):
        RES_ALL = 0
        RES_VIS = 1
        RES_SEP = 3
        RES_OK = 4
        
        res = app.dlg_custom(_('Save editors to a single file'),
            410, 175,
            '\n'.join([
                'type=radio\1cap='+_('Save all tabs (including not visible)')+'\1pos=10,10,400,0\1val=1',    
                'type=radio\1cap='+_('Save visible editors in all groups')+'\1pos=10,35,400,0',
                'type=label\1cap='+_('Separator line:')+'\1pos=10,65,400,0',    
                'type=edit\1val=-----\1pos=10,90,400,0',
                'type=button\1cap='+_('&OK')+'\1pos=100,140,200,0',    
                'type=button\1cap='+_('Cancel')+'\1pos=210,140,310,0'    
            ]),
            get_dict=True
            )
        if res is None: return
        if res['clicked']!=RES_OK: return
        
        res_all = res[RES_ALL]=='1'
        res_sep = res[RES_SEP]
    
        if res_all:
            eds = [app.Editor(h) for h in app.ed_handles()]
        else:
            MAX_GROUPS = 6
            eds = [app.ed_group(i) for i in range(MAX_GROUPS)]
            eds = [i for i in eds if i]
        
        fn = app.dlg_file(False, _('saved.txt'), '', '')
        if not fn:
            return 
            
        txt = ('\n'+res_sep+'\n').join([e.get_text_all() for e in eds])
        with open(fn, 'w', encoding='utf8') as f:
            f.write(txt)
        app.msg_status(_('Saved: ')+fn)
       #def save_tabs_to_file
    
    def remove_unprinted(self):
        body    = ed.get_text_all()
        in_size = len(body)
        for ichar in range(32):
            if not ichar in [9,10,13]:
                body    = body.replace(chr(ichar), '')
        ed.set_text_all(body)   if in_size != len(body) else None
        app.msg_status(f(_('Removed characters: {}'), in_size-len(body)))
       #def remove_unprinted

    def remove_lines_by_callback(self, callback):
        carets = ed.get_carets()
        cnt = 0
        for i in reversed(range(ed.get_line_count())):
            l = ed.get_text_line(i)
            if bool(l) and callback(l):
                ed.delete(0, i, 0, i+1)
                cnt += 1
        if cnt:
            app.msg_status(_('Removed {} line(s)').format(cnt))
            if carets:
                x, y, x1, y1 = carets[0]
                y_max = ed.get_line_count()-1
                if max(y, y1) > y_max:
                    ed.set_caret(0, y_max)
        else:
            app.msg_status(_('No lines with "{}" were found').format(s))

    def remove_lines_with(self):
        s = app.dlg_input(_('Remove lines containing text:'), '')
        if not s: return # empty str not allowed
        self.remove_lines_by_callback(lambda l: s in l)
        
    def remove_lines_regex(self):
        s = app.dlg_input(_('Remove lines containing RegEx:'), '')
        if not s: return # empty str not allowed
        try:
            s_re = re.compile(s, 0)
            self.remove_lines_by_callback(lambda l: s_re.search(l) is not None)
        except:
            app.msg_status(_('Incorrect RegEx: ')+s) 

    def remove_xml_tags(self):
        rxCmt   = re.compile('<!--.*?-->', re.DOTALL)
        rxTag   = re.compile(r'''<\w+('.*?'|".*?"|.)*?>''', re.DOTALL)
        body    = ed.get_text_all()
        if not rxCmt.search(body) and not rxTag.search(body):
            return app.msg_status(_('No tags were found'))
        cmts    = rxCmt.findall(body)
        body    = rxCmt.sub('', body)
        tags    = rxTag.findall(body)
        body    = rxTag.sub('', body)
        ed.set_text_all(body)
        app.msg_status(
            f(_('Removed {} tag(s)'), len(tags))
                if not cmts else
            f(_('Removed {} comment(s), {} tag(s)'), len(cmts), len(tags))
        )
       #def remove_xml_tags
       
    @staticmethod
    def exec_selected_in_console(): # halfbrained @github
        if len(ed.get_carets()) > 1: return app.msg_status(_('Only for single caret/selection'))
        cmd = None
        txt = ed.get_text_sel()
        if txt:
            if '\n' not in txt:
                cmd = txt
        else:
            caret = ed.get_carets()[0]
            caret_x,caret_y = caret[0:2]
            cmd = ed.get_text_line(caret_y)
            if caret_y < ed.get_line_count()-1:
                ed.set_caret(caret_x, caret_y+1)
        if cmd:
            print('>>> ' + cmd)
            app.app_proc(app.PROC_EXEC_PYTHON, 'from cudatext import *')
            app.app_proc(app.PROC_EXEC_PYTHON, cmd)
       #def exec_selected_in_console
    
    def on_console_nav(self, ed_self, text):    return Nav_cmds.on_console_nav(ed_self, text)
    def _open_file_near(self, where='right'):   return Nav_cmds._open_file_near(where)
    def open_selected(self):                    return Nav_cmds.open_selected()
    def nav_by_console_err(self):               return Nav_cmds.nav_by_console_err()
    
    def add_indented_line_above(self):          return Insert_cmds.add_indented_line_above()
    def add_indented_line_below(self):          return Insert_cmds.add_indented_line_below()
    def indent_and_surround(self, bfr, aft):    return Insert_cmds.indent_and_surround(bfr, aft)
    def paste_to_1st_col(self):                 return Insert_cmds.paste_to_1st_col()
    def paste_with_indent(self, where='above'): return Insert_cmds.paste_with_indent(where)
    def paste_trimmed(self):                    return Insert_cmds.paste_trimmed()
    def trim_sel(self, mode):                   return Insert_cmds.trim_sel(mode)
    def fill_by_str(self):                      return Insert_cmds.fill_by_str()
    def copy_unicode_char_name(self):           return Insert_cmds.copy_unicode_char_name()
    def insert_char_by_hex(self):               return Insert_cmds.insert_char_by_hex()
    
    def copy_term(self):                        return SCBs.copy_term()
    def replace_term(self):                     return SCBs.replace_term()
    def expand_sel(self):                       return SCBs.expand_sel(copy=False)
    def expand_sel_copy(self):                  return SCBs.expand_sel(copy=True)
    
    def scroll_to(self, place):                             return Jumps_cmds.scroll_to(place)
    def jump_to_matching_bracket(self):                     return Jumps_cmds.jump_to_matching_bracket()
    def jump_to_status_line(self, status, nx_pr, bgn_end):  return Jumps_cmds.jump_to_status_line(status, nx_pr, bgn_end)
    def jump_to_line_by_cb(self):                           return Jumps_cmds.jump_to_line_by_cb()
    def jump_ccsc(self, drct, sel):                         return Jumps_cmds.jump_ccsc(drct, sel)
    def dlg_bms_in_tab(self):                               return Jumps_cmds.dlg_bms_in_tab()
    def dlg_bms_in_tabs(self, what='a'):                    return Jumps_cmds.dlg_bms_in_tabs(what)
    def jump_staple(self, what='end'):                      return Jumps_cmds.jump_staple(what)
    
    def go_prgph(self, what):                               return Prgph_cmds.go_prgph(what)
    def align_prgph(self, how):                             return Prgph_cmds.align_prgph(how)
   #class Command


def fnd_mtch_char(ed4find, c_opn, c_cls, line, col, row, to_end):
    """ Find paired char c_opn from (col, row) in dir to_end and
            skip inside pair (c_opn, c_cls)
    """
    assert line     ==ed4find.get_text_line(row)
#   assert line[col]==c_opn
    pass;                      #LOG and log('c_opn, c_cls, line[col-1:col+2], col, row, to_end={}',(c_opn, c_cls, line[col-1:col+2], col, row, to_end))
    cnt = 1
    while True:
        for pos in (range(col, len(line)) if to_end else
                    range(col, -1, -1)):
            c = line[pos]
            if False:
                pass
            elif c == c_opn:
                cnt = cnt + 1
            elif c == c_cls:
                cnt = cnt - 1
            else:
                continue  # for pos
            pass;              #LOG and log('line, pos, c, cnt={}', (line, pos, c, cnt))
            if 0 == cnt:
                # Found!
                col = pos
                break#for pos
           #for pos
        if 0 == cnt:
            break#while
        if to_end:
            row = row + 1
            if row == ed4find.get_line_count():
                pass;          #LOG and log('not found')
                break#while
            line = ed4find.get_text_line(row)
            col = 0
        else:
            if row == 0:
                pass;          #LOG and log('not found')
                break#while
            row = row - 1
            line = ed4find.get_text_line(row)
            col = len(line) - 1
       #while
    return (c_opn, c_cls, col, row) if cnt == 0 else (c_opn, c_cls, -1, -1)
   #def fnd_mtch_char
#NOTE: mcth
def find_matching_char(ed4find, cStart, rStart, opn2cls={'[':']', '{':'}', '(':')', '<':'>', '«':'»'}):
    ''' Find matching (pair) char for char from position (cStart,rStart) (or prev) 
    '''
    cls2opn = {c:o for o,c in opn2cls.items()}
    
    crt_line=  ed4find.get_text_line(rStart)
    # Is there any bracket AFTER caret?
    c_aft   = crt_line[cStart]   if cStart<len(crt_line) else ' '
    c_bfr   = crt_line[cStart-1] if cStart>0             else ' '
    pass;                      #LOG and log('c_bfr, c_aft={}', (c_bfr, c_aft))

    if False:pass
    elif c_aft in opn2cls: (c_opn, c_cls, col) = (c_aft, opn2cls[c_aft], cStart+1)
    elif c_aft in cls2opn: (c_opn, c_cls, col) = (c_aft, cls2opn[c_aft], cStart-1)
    elif c_bfr in opn2cls: (c_opn, c_cls, col) = (c_bfr, opn2cls[c_bfr], cStart  )
    elif c_bfr in cls2opn: (c_opn, c_cls, col) = (c_bfr, cls2opn[c_bfr], cStart-2)
    else: return (c_aft, '', -1, -1)

    to_end  = c_opn in opn2cls
    line    = crt_line
    row     = rStart
    pass;                      #LOG and log('c_opn,c_cls,to_end,col={}', (c_opn,c_cls,to_end,col))
    c_opn,  \
    c_cls,  \
    col,row = fnd_mtch_char(ed4find, c_opn, c_cls, line, col, row, to_end)
    return c_opn, c_cls, col, row
#   return (c_opn, c_cls, col, row) if cnt==0 else (c_opn, c_cls, -1, -1)
   #def find_matching_char

def get_word_or_quoted(text, start, not_word_chars='[](){}', quot_chars="'"+'"'):      # '"
    ''' Find word or 'smth' or "smth" around start.
        Return      (found, pos_of_found)
    '''
    if not text or not(0<=start<=len(text)):   return ('', -1)
    text        = ' '+text+' '
    start       = start+1
    bgn, end    = -1, -1
    left_cond   = ' '
    # Backward
    pos         = start-1
    while 0<=pos:
        c       = text[pos]
        if c.isspace() or c in not_word_chars:
            left_cond   = ' '
            bgn         = pos+1
            break
        if c in quot_chars:
            left_cond   = c
            bgn         = pos+1
            break
        pos    -= 1
    # Forward
    pos         = start
    while pos<len(text):
        c       = text[pos]
        if left_cond==' ' and (c.isspace() or c in not_word_chars):
            end         = pos
            break
        if left_cond!=' ' and c in quot_chars:
            end         = pos
            break
        pos    += 1
    
    return (text[bgn:end], bgn-1) if bgn!=-1 and end!=-1 else ('', -1)
   #def get_word_or_quoted

#######################################
if __name__ == '__main__' :     # Tests
    pass;                      #log('test')
#   Prgph_cmds.go_prgph('bgn')
#   Prgph_cmds.go_prgph('end')
#   Prgph_cmds.go_prgph('nxt')
#   Prgph_cmds.go_prgph('prv')
#   Prgph_cmds.align_prgph('l')

'''
ToDo
[+][kv-kv][20nov15] Вставить строку с отступом под/над текущей
[+][kv-kv][20nov15] Activate tab #1, #2, ..., #9 Activate tab on 2nd group #1, #2, ..., #9
[+][kv-kv][20nov15] Paste from clipboard, to 1st column: paste_to_1st_col
[?][kv-kv][20nov15] Paste from clipboard, to 1st column for m-carets
[+][kv-kv][20nov15] Find string from clipboard - next/prev: find_cb_string_next
[+][kv-kv][20nov15] Jump to matching bracket: jump_to_matching_bracket
[+][kv-kv][20nov15] CopyTerm, ReplaceTerm
[-][kv-kv][20nov15] Comment/uncomment before cur term (or fix col?)
[+][kv-kv][24nov15] Wrap for "Find string from clipboard"
[+][kv-kv][25nov15] Replace all as selected to cb-string: replace_all_sel_to_cb
[+][kv-kv][25nov15] Open selected file: open_selected
[+][kv-kv][25nov15] Catch on_console_nav
[+][kv-kv][26nov15] Scroll on_console_nav, Find*
[+][at-kv][09dec15] Refactor: find_pair
[+][kv-kv][15dec15] Find cb-string via cmd_FinderAction (for use next/prev after)
'''
