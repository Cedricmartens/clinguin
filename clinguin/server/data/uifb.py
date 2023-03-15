"""
Module that contains the UIFB class.
"""
import logging
import clorm

from clorm import Raw
from clingo import Control,parse_term
from clingo.symbol import Function, Number, String

from clinguin.utils import NoModelError, Logger

from .element import ElementDao
from .attribute import AttributeDao
from .callback import CallbackDao

def symbols_to_facts(symbols):
    return "\n".join([str(s)+"." for s in symbols])

MENU_BAR = """
element(m, menu_bar, window).
element(menu_options, menu_bar_section, m).
attribute(menu_options, label, "Options").
element(menu_options_clear, menu_bar_section_item, menu_options).
attribute(menu_options_clear, label, "Clear").
attribute(menu_options_clear, accelerator, "Cmd+C").
callback(menu_options_clear, click, clear_assumptions).
element(menu_options_next, menu_bar_section_item, menu_options).
attribute(menu_options_next, label, "Next").
attribute(menu_options_next, accelerator, "Cmd+N").
callback(menu_options_next, click, next_solution).
element(menu_options_select, menu_bar_section_item, menu_options).
attribute(menu_options_select, label, "Select").
attribute(menu_options_select, accelerator, "Cmd+S").
callback(menu_options_select, click, select)."""


class UIFB:
    """
    The UIFB is the low-level-access-class for handling clorm and clingo, regarding brave-cautious and other default things. This class provides functionality to create a factbase with brave-cautious extended files, functionality to query important things for clinguin, etc.
    """

    unifiers = [ElementDao, AttributeDao, CallbackDao]

    def __init__(self, ui_files,cautious_tag="_c",brave_tag="_b",auto_tag=None, include_menu_bar=False):
        self._logger = logging.getLogger(Logger.server_logger_name)
        self._ui_files = ui_files
        self._tags = {"cautious":cautious_tag,"brave":brave_tag,"auto":auto_tag}
        self._conseq ={
            "cautious": None,
            "brave": None,
            "auto": None
        }
        self.clear_all()
        self._factbase = None
        self._include_menu_bar = include_menu_bar

    def __str__(self):
        s = "\nConsequences:\n==========\n"
        for k,v in self._conseq.items():
            outdated = "OUTDATED!" if self._outdated[k] else ""
            s+= f"{k} consequences: (tagged with {self._tags[k]}) {outdated}\n"
            s+=" ".join([str(s) for s in v])
            s+="\n"
        s +=  "\nUI Factbase:\n=========\n"
        s += self._factbase.asp_str()
        return s

    @property
    def is_empty(self):
        return self._factbase is None

    def clear_all(self):
        self._outdated ={
            "cautious": True,
            "brave": True,
            "auto": True
        }

    def tag(self, symbols, tag):
        if tag is None:
            return symbols
        tagged = []
        for s in symbols:
            tagged.append(Function(tag,[s]))
        return tagged

    @property
    def conseq_facts(self):
        conseq_facts = ""
        for c_type, symbols in self._conseq.items():
            if symbols is None:
                raise RuntimeError("Use update function before getting the program")
            if self._outdated[c_type]:
                self._logger.warn(f"The {c_type} consequence facts are outdated. Make sure this is intended.")
            conseq_facts += symbols_to_facts(self.tag(symbols,self._tags[c_type]))

        return conseq_facts

    def _set_fb_symbols(self, symbols):
        self._factbase = clorm.unify(self.unifiers, symbols)

    def ui_control(self, extra_ui_prg=""):
        """
        Generates a ClingoControl Object from paths of ui files and extra parts of a logic program given by a string.
        """
        uictl = Control(['0','--warn=none'])
        for f in self._ui_files:
            try:
                uictl.load(str(f))
            except Exception as e:
                self._logger.critical("File %s  could not be loaded - likely not existant or syntax error in file!", str(f))
                raise e
        if self._include_menu_bar:
            uictl.add("base",[],MENU_BAR)

        uictl.add("base",[],extra_ui_prg)
        uictl.add("base",[],self.conseq_facts)
        uictl.add("base",[],"#show element/3. #show attribute/3. #show callback/3.")
        uictl.ground([("base",[])])

        return uictl

    def set_auto_conseq(self, model_symbols):
        self._conseq["auto"] = model_symbols
        self._outdated["auto"] = False

    def update_all_consequences(self, ctl, assumptions=None, clear=True):
        if clear:
            self.clear_all()

        c_types=["brave","cautious","auto"]
        for c_type in c_types:
            self.update_cosequence(c_type, ctl, assumptions)

    def update_uifb(self, extra_ui_prg=""):
        uictl = self.ui_control(extra_ui_prg)

        with uictl.solve(yield_=True) as result:
            for m in result:
                model_symbols = m.symbols(shown=True)
                break

        self._factbase = clorm.unify(self.__class__.unifiers, model_symbols)

    def update(self, ctl, assumptions=None, clear=True, extra_ui_prg=""):
        self.update_all_consequences(ctl, assumptions, clear)
        self.update_uifb(extra_ui_prg)

    def _compute_consequences(self,ctl, assumptions):
        with ctl.solve(assumptions=[(a,True) for a in assumptions],
                yield_=True) as result:
            model_symbols = None
            for m in result:
                model_symbols = m.symbols(shown=True,atoms=False)
            if model_symbols is None:
                self._logger.error("Got an UNSAT result with the given encoding.")
                self._logger.error("The operation can't be performed")
                raise NoModelError(core=result.core())
        return list(model_symbols)

    def update_cosequence(self, c_type, ctl, assumptions=None):
        if not self._outdated[c_type]:
            self._logger.debug(f"Skiping {c_type} consequences")
            return
        self._logger.debug(f"Updating {c_type} consequences")
        if c_type in ["brave","cautious"]:
            ctl.configuration.solve.opt_mode = 'ignore'
        ctl.configuration.solve.enum_mode = c_type
        self._conseq[c_type] = self._compute_consequences(ctl, assumptions)
        self._outdated[c_type]=False

    def add_message(self,title,message,type="info"):
        """
        Adds a ''Message'' (aka. Notification/Pop-Up) for the user with a certain title and message.
        """
        self.add_element("message","message","window")
        self.add_attribute("message","title",title)
        self.add_attribute("message","message",message)
        self.add_attribute("message","type",type)


    # Manage factbase

    def add_element(self, id, t, parent):
        if type(id)==str:
            id = Function(id,[])
        if type(t)==str:
            t = Function(t,[])
        if type(parent)==str:
            parent = Function(parent,[])
        self._factbase.add(ElementDao(Raw(id),Raw(t),Raw(parent)))

    def add_attribute(self, id, key, value):
        if type(id)==str:
            id = Function(id,[])
        if type(key)==str:
            key = Function(key,[])
        if type(value)==str:
            value = String(value)
        if type(value)==int:
            value = Number(value)
        self._factbase.add(AttributeDao(Raw(id),Raw(key),Raw(value)))

    def get_elements(self):
        return self._factbase.query(ElementDao).all()

    def get_attributes(self):
        return self._factbase.query(AttributeDao).all()

    def get_attributesGrouped(self):
        return self._factbase.query(AttributeDao).group_by(AttributeDao.id).all()

    def get_callbacksGrouped(self):
        return self._factbase.query(CallbackDao).group_by(CallbackDao.id).all()

    def get_callbacks(self):
        return self._factbase.query(CallbackDao).all()

    def get_attributesForElementId(self, element_id):
        return self._factbase.query(AttributeDao).where(
            AttributeDao.id == element_id).all()

    def get_callbacksForElementId(self, element_id):
        return self._factbase.query(CallbackDao).where(
            CallbackDao.id == element_id).all()