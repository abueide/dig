from abc import ABCMeta
import pdb
import random
import os.path
from time import time

import sage.all

import vcommon as CM
import settings
from miscs import Miscs

from ds import Inps, Traces, DTraces, Prog
from invs import EqtInv, IeqInv, Invs, DInvs
from symstates import SymStates
from cegir import Cegir
import srcJava

dbg = pdb.set_trace

mlog = CM.getLogger(__name__, settings.logger_level)


class Dig(object):
    __metaclass__ = ABCMeta

    def __init__(self, filename):
        assert os.path.isfile(filename), filename
        mlog.info("analyze '{}'".format(filename))
        self.filename = filename

    @property
    def tmpdir(self):
        try:
            return self._tmpdir
        except AttributeError:
            import tempfile
            self._tmpdir = tempfile.mkdtemp(
                dir=settings.tmpdir, prefix="Dig_")
            return self._tmpdir

    def start(self, seed, maxdeg):
        assert maxdeg is None or maxdeg >= 1, maxdeg

        random.seed(seed)
        sage.all.set_random_seed(seed)
        mlog.debug("set seed to: {} (test {})".format(
            seed, sage.all.randint(0, 100)))

        # determine degree
        maxvars = max(self.inv_decls.itervalues(), key=lambda d: len(d))
        self.deg = Miscs.get_auto_deg(maxdeg, len(maxvars), settings.MAX_TERM)

    def sanitize(self, dinvs, dtraces):
        if dinvs.siz:
            mlog.info("test {} invs on {} dtraces".format(
                dinvs.siz, dtraces.siz))
            dinvs = dinvs.test(dtraces)
            if dinvs.siz:
                mlog.info("uniqify {} invs".format(dinvs.siz))
                mlog.debug("{}".format(dinvs.__str__(print_stat=True)))
                dinvs = dinvs.uniqify(self.inv_decls.use_reals)

        return dinvs

    def print_results(self, dinvs, dtraces, inps, st):
        result = ("*** '{}', {} locs, "
                  "invs {} ({} eqts), traces {}, inps {}, "
                  "time {:02f} s, rand {}:\n{}")
        print(result.format(self.filename, len(dinvs),
                            dinvs.siz, dinvs.n_eqs, dtraces.siz,
                            len(inps) if inps else 0,
                            time() - st, sage.all.randint(0, 100),
                            dinvs.__str__(print_stat=True)))


class DigCegir(Dig):
    def __init__(self, filename):
        super(DigCegir, self).__init__(filename)

        # call ASM to obtain
        (inp_decls, inv_decls, clsname, mainQName, jpfdir, jpffile,
         tracedir, traceFile) = srcJava.parse(filename, self.tmpdir)

        self.inp_decls = inp_decls
        self.inv_decls = inv_decls
        self.useRandInit = True

        exe_cmd = settings.JAVA_RUN(tracedir=tracedir, clsname=clsname)
        self.prog = Prog(exe_cmd, inv_decls)

        self.symstates = SymStates(inp_decls, inv_decls)
        self.symstates.compute(self.filename, mainQName, clsname, jpfdir)

        # remove locations with no symbolic states
        invalid_locs = [loc for loc in inv_decls
                        if loc not in self.symstates.ss]
        for loc in invalid_locs:
            self.inv_decls.pop(loc)

    def str_of_locs(self, locs):
        return '; '.join("{} ({})".format(l, self.inv_decls[l]) for l in locs)

    def start(self, seed, maxdeg, do_eqts, do_ieqs, do_preposts):
        super(DigCegir, self).start(seed, maxdeg)

        st = time()
        solver = Cegir(self.symstates, self.prog)
        mlog.debug("check reachability")
        dinvs, dtraces, inps = solver.check_reach()
        if not dtraces:
            return dinvs, dtraces, self.tmpdir

        def _infer(typ, f):
            mlog.info("gen {} at {} locs".format(typ, len(dtraces)))
            mlog.debug(self.str_of_locs(dtraces.keys()))

            st = time()
            invs = f()
            if not invs:
                mlog.warn("infer no {}".format(typ))
            else:
                mlog.info("infer {} {} in {}s".format(
                    invs.siz, typ, time() - st))
                dinvs.merge(invs)
                mlog.debug("{}".format(dinvs.__str__(print_stat=True)))

        if do_eqts:
            _infer('eqts', lambda: self.infer_eqts(self.deg, dtraces, inps))
        if do_ieqs:
            _infer('ieqs', lambda: self.infer_ieqs(dtraces, inps))

        dinvs = self.sanitize(dinvs, dtraces)

        if do_preposts:
            _infer('preposts', lambda: self.infer_preposts(dinvs, dtraces))

        self.print_results(dinvs, dtraces, inps, st)

        tracefile = os.path.join(self.tmpdir, settings.TRACE_DIR, 'all.tcs')
        dtraces.vwrite(self.inv_decls, tracefile)

        return dinvs, dtraces, self.tmpdir

    def infer_eqts(self, deg, dtraces, inps):
        from cegirEqts import CegirEqts
        solver = CegirEqts(self.symstates, self.prog)
        solver.useRandInit = self.useRandInit
        dinvs = solver.gen(self.deg, dtraces, inps)
        return dinvs

    def infer_ieqs(self, dtraces, inps):
        from cegirIeqs import CegirIeqs
        solver = CegirIeqs(self.symstates, self.prog)
        dinvs = solver.gen(dtraces, inps)
        return dinvs

    def infer_preposts(self, dinvs, dtraces):
        from cegirPrePosts import CegirPrePosts
        solver = CegirPrePosts(self.symstates, self.prog)
        dinvs = solver.gen(dinvs, dtraces)
        return dinvs


class DigTraces(Dig):
    def __init__(self, tracefile):
        super(DigTraces, self).__init__(tracefile)

        self.inv_decls, self.dtraces = DTraces.vread(tracefile)

    def start(self, seed, maxdeg, do_eqts, do_ieqs, do_preposts):

        super(DigTraces, self).start(seed, maxdeg)

        st = time()
        dinvs = DInvs()
        for loc in self.dtraces:
            dinvs[loc] = Invs()
            traces = self.dtraces[loc]
            symbols = self.inv_decls[loc]
            if do_eqts:
                terms, template, uks, nEqtsNeeded = Miscs.initTerms(
                    symbols.names, self.deg, settings.EQT_RATE)
                exprs = list(traces.instantiate(template, nEqtsNeeded))
                eqts = Miscs.solveEqts(exprs, uks, template)
                for eqt in eqts:
                    dinvs[loc].add(EqtInv(eqt))

            if do_ieqs:
                maxV = settings.OCT_MAX_V
                minV = -1*maxV

                oct_siz = 2
                terms = Miscs.get_terms_fixed_coefs(symbols.sageExprs, oct_siz)
                for t in terms:
                    upperbound = max(traces.myeval(t))
                    if upperbound > maxV or upperbound < minV:
                        continue

                    ieq = t <= upperbound
                    dinvs[loc].add(IeqInv(ieq))

        dinvs = self.sanitize(dinvs, self.dtraces)
        self.print_results(dinvs, self.dtraces, None, st)
        return dinvs, None, self.tmpdir
