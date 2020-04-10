import pdb
import sys
import datetime
import time
import helpers.vcommon
from pathlib import Path

DBG = pdb.set_trace


def run(ifile, seed, args):
    import alg
    if ifile.suffix == ".java" or ifile.suffix == ".class":
        if (args.se_mindepth and args.se_mindepth >= 1 and
                args.se_mindepth != settings.Java.SE_MIN_DEPTH):
            settings.Java.SE_MIN_DEPTH = args.se_mindepth
        dig = alg.DigSymStatesJava(ifile)
    elif ifile.suffix == ".c":
        if (args.se_mindepth and args.se_mindepth >= 1 and
                args.se_mindepth != settings.C.SE_MIN_DEPTH):
            settings.C.SE_MIN_DEPTH = args.se_mindepth
        dig = alg.DigSymStatesC(ifile)
    else:
        # traces file(s)
        test_tracefile = Path(
            args.test_tracefile) if args.test_tracefile else None
        dig = alg.DigTraces(ifile, test_tracefile)

    return dig.start(seed=seed, maxdeg=args.maxdeg)


if __name__ == "__main__":
    import argparse
    aparser = argparse.ArgumentParser("DIG")
    ag = aparser.add_argument
    ag("inp", help=("input file (.c, .java. , .class, trace_text_file) "
                    "for invariant generation or result directory for analysis"))

    # 0 Error #1 Warn #2 Info #3 Debug #4 Detail
    ag("--log_level", "-log_level",
       type=int,
       choices=range(5),
       default=2,
       help="set logger info")

    ag("--seed", "-seed",
       type=float,
       help="use this seed")

    ag("--maxdeg", "-maxdeg",
       type=int,
       default=None,
       help="find nonlinear invs up to degree")

    ag("--maxterm", "-maxterm",
       type=int,
       default=None,
       help="autodegree")

    ag("--inpMaxV", "-inpMaxV",
       type=int,
       help="max inp value")

    ag("--se_mindepth", "-se_mindepth",
       type=int,
       help="depthlimit of symbolic execution")

    ag("--octmaxv", "-octmaxv",
       type=int,
       help="max val for oct ieqs")

    ag("--eqtrate", "-eqtrate",
       type=float,
       help="Equation rate multiplier")

    ag("--noss", "-noss",
       action="store_true",
       help="don't use symbolic states, i.e., just dynamic analysis")

    ag("--noeqts", "-noeqts",
       action="store_true",
       help="don't compute eq invariants")

    ag("--noieqs", "-noieqs",
       action="store_true",
       help="don't compute ieq/oct invariants")

    ag("--nominmaxplus", "-nominmaxplus",
       action="store_true",
       help="don't compute min/max-plus invariants")

    ag("--nopreposts", "-nopreposts",
       action="store_true",
       help="don't compute prepost specs")

    ag("--nomp", "-nomp",
       action="store_true",
       help="don't use multiprocessing")

    ag("--normtmp", "-normtmp",
       action="store_true")

    ag("--test_tracefile", "-test_tracefile",
       type=str,
       default=None,
       help="tracefile to test")

    ag("-uterms", "--uterms",
       type=str,
       default=None,
       help="user-supplied terms (separated by space), e.g., \"-uterms y^2 xy\"")

    ag("--benchmark_times", "-benchmark_times",
       type=int,
       default=None,
       help="run Dig this many times")

    ag("--benchmark_dir", "-benchmark_dir",
       type=str,
       default=None,
       help="store benchmark results in this dir")

    args = aparser.parse_args()

    import settings
    settings.DO_SS = not args.noss
    settings.DO_MP = not args.nomp
    settings.DO_EQTS = not args.noeqts
    settings.DO_IEQS = not args.noieqs
    settings.DO_MINMAXPLUS = not args.nominmaxplus
    settings.DO_PREPOSTS = not args.nopreposts
    settings.DO_RMTMP = not args.normtmp

    if 0 <= args.log_level <= 4 and args.log_level != settings.logger_level:
        settings.logger_level = args.log_level
    settings.logger_level = helpers.vcommon.getLogLevel(settings.logger_level)

    mlog = helpers.vcommon.getLogger(__name__, settings.logger_level)
    if (args.inpMaxV and args.inpMaxV >= 1 and
            args.inpMaxV != settings.INP_MAX_V):
        settings.INP_MAX_V = args.inpMaxV

    if (args.eqtrate and args.eqtrate >= 1 and
            args.eqtrate != settings.EQT_RATE):
        settings.EQT_RATE = args.eqtrate

    if (args.octmaxv and args.octmaxv >= 1 and
            args.octmaxv != settings.OCT_MAX_V):
        settings.OCT_MAX_V = args.octmaxv

    if (args.maxterm and args.maxterm >= 1 and
            args.maxterm != settings.MAX_TERM):
        settings.MAX_TERM = args.maxterm

    if args.uterms:
        settings.UTERMS = set(args.uterms.split())

    mlog.info("{}: {}".format(datetime.datetime.now(), ' '.join(sys.argv)))

    if __debug__:
        mlog.warning("DEBUG MODE ON. Can be slow !")

    seed = round(time.time(), 2) if args.seed is None else float(args.seed)

    inp = Path(args.inp)

    def run_f(ifile, seed):
        return run(ifile, seed, args)

    if inp.is_dir():
        from analysis import Benchmark
        benchmark = Benchmark(inp, args)
        if args.benchmark_times:
            benchmark.run(run_f)
        else:
            benchmark.analyze()
        exit(0)
    else:
        if not inp.is_file():
            mlog.error("'{}' is not a valid file!".format(inp))
            exit(1)
        run_f(inp, seed)
