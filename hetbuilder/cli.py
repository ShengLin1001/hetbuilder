#!/usr/bin/env python
from matplotlib.pyplot import step
import typer
from typer.params import Option, Argument
from typing import Optional, Tuple, List

from hetbuilder import __version__, CoincidenceAlgorithm, Interface, InteractivePlot
from hetbuilder.log import logger, set_verbosity_level
from hetbuilder.atom_checks import check_atoms

from pathlib import Path

import ase.io

import numpy as np


app = typer.Typer(add_completion=True)


def version_callback(value: bool):
    if value:
        typer.echo(f"Hetbuilder Version: {__version__}")
        raise typer.Exit()


@app.callback(
    help=typer.style(
        """Builds 2D heterostructure interfaces via coincidence lattice theory.\n    
            Github repository: https://github.com/romankempt/hetbuilder\n
            Documentation: https://hetbuilder.readthedocs.io/en/latest\n
            Available under the MIT License. Please cite 10.5281/zenodo.4721346.""",
        fg=typer.colors.GREEN,
        bold=False,
    )
)
def callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    )
):
    pass


@app.command(
    context_settings={"allow_extra_args": False, "ignore_unknown_options": False},
    help=typer.style(
        """Build interfaces and show results interactively.""",
        fg=typer.colors.GREEN,
        bold=False,
    ),
)
def build(
    ctx: typer.Context,
    lower: Path = typer.Argument(..., help="Path to lower layer structure file."),
    upper: Path = typer.Argument(..., help="Path to upper layer structure file."),
    Nmax: int = typer.Option(
        10, "-N", "--Nmax", help="Maximum number of translations."
    ),
    Nmin: int = typer.Option(0, "--Nmin", help="Minimum number of translations."),
    angle_stepsize: float = typer.Option(
        1, "-as", "--angle_stepsize", help="Increment of angles to look through."
    ),
    angle_limits: Tuple[float, float] = typer.Option(
        (0, 90),
        "-al",
        "--angle_limits",
        help="Lower and upper bound of angles too look through with given step size.",
    ),
    angles: List[float] = typer.Option(
        [],
        "-a",
        "--angle",
        help="Explicitely set angle to look for. Can be called multiple times.",
    ),
    tolerance: float = typer.Option(
        0.1,
        "-t",
        "--tolerance",
        help="Tolerance criterion to accept matching lattice points in Angström.",
    ),
    weight: float = typer.Option(
        0.5,
        "-w",
        "--weight",
        help="Weight of the coincidence unit cell, given by C=A+weight*(B-A).",
    ),
    distance: float = typer.Option(
        4, "-d", "--distance", help="Interlayer distance of the heterostructure in Angström."
    ),
    vacuum: float = typer.Option(
        15, "-v", "--vacuum", help="Thickness of the vacuum layer of the heterostructure in Angström."
    ),
    no_idealize: bool = typer.Option(
        False, "--no_idealize", help="Disable idealize lattice parameters via spglib."
    ),
    symprec: float = typer.Option(
        1e-5, "-sp", "--symprec", help="Symmetry precision for spglib."
    ),
    angle_tolerance: float = typer.Option(
        5, "--angle_tolerance", help="Angle tolerance for spglib."
    ),
    verbosity: int = typer.Option(
        1, "--verbosity", "-V", count=True, help="Set verbosity level."
    ),
) -> None:
    """Builds heterostructure interface for given choice of parameters.

    Example:
        hetbuilder build graphene.xyz MoS2.xyz -N 10 -al 0 30 -as 0.1
    """
    set_verbosity_level(verbosity)
    bottom = ase.io.read(lower)
    top = ase.io.read(upper)
    logger.info(
        "Building heterostructures from {} and {}.".format(
            bottom.get_chemical_formula(), top.get_chemical_formula()
        )
    )

    alg = CoincidenceAlgorithm(bottom, top)
    results = alg.run(
        Nmax=Nmax,
        Nmin=Nmin,
        angles=angles,
        angle_limits=angle_limits,
        angle_stepsize=angle_stepsize,
        tolerance=tolerance,
        distance=distance,
        vacuum=vacuum,
        no_idealize=no_idealize,
        symprec=symprec,
        angle_tolerance=angle_tolerance,
        verbosity=verbosity,
    )
    if results is not None:
        ip = InteractivePlot(bottom, top, results, weight)
        ip.plot_results()


@app.command(
    context_settings={"allow_extra_args": False, "ignore_unknown_options": False},
    help=typer.style(
        """Find lowest-stress coincidence unit cell.""",
        fg=typer.colors.GREEN,
        bold=False,
    ),
)
def match(
    lower: Path = typer.Argument(..., help="Path to lower layer structure file."),
    upper: Path = typer.Argument(..., help="Path to upper layer structure file."),
    Nmax: int = typer.Option(
        10, "-N", "--Nmax", help="Maximum number of translations."
    ),
    Nmin: int = typer.Option(0, "--Nmin", help="Minimum number of translations."),
    angles: List[float] = typer.Option(
        [],
        "-a",
        "--angle",
        help="Explicitely set angle to look for. Can be called multiple times.",
    ),
    weight: float = typer.Option(
        0.5,
        "-w",
        "--weight",
        help="Weight of the coincidence unit cell, given by C=A+weight*(B-A).",
    ),
    distance: float = typer.Option(
        4, "-d", "--distance", help="Interlayer distance of the heterostructure in Angström."
    ),
    vacuum: float = typer.Option(
        15, "-v", "--vacuum", help="Thickness of the vacuum layer of the heterostructure in Angström."
    ),    
    no_idealize: bool = typer.Option(
        False, "--no_idealize", help="Disable idealize lattice parameters via spglib."
    ),
    symprec: float = typer.Option(
        1e-5, "-sp", "--symprec", help="Symmetry precision for spglib."
    ),
    angle_tolerance: float = typer.Option(
        5, "--angle_tolerance", help="Angle tolerance for spglib."
    ),
    verbosity: int = typer.Option(
        1, "--verbosity", "-V", count=True, help="Set verbosity level."
    ),
):
    """Matches two structures to find lowest-stress coincidence lattice.

    Automatically checks different tolerance values.

    Example:
        hetbuilder match graphene.xyz MoS2.xyz
    """
    bottom = ase.io.read(lower)
    top = ase.io.read(upper)
    logger.info(
        "Building heterostructure from {} and {}.".format(
            bottom.get_chemical_formula(), top.get_chemical_formula()
        )
    )
    alg = CoincidenceAlgorithm(bottom, top)
    set_verbosity_level(verbosity)
    if angles == []:
        angles = list(range(0, 91, 1))

    def circle_loop(
        tolerance_stepsize=0.05,
        max_tolerance=0.2,
        distance=distance,
        vacuum=vacuum,
        angles=angles,
        no_idealize=no_idealize,
        symprec=symprec,
        angle_tolerance=angle_tolerance,
        weight=weight,
    ):
        interfaces = []
        # outer loop over different tolerances
        for j, t in enumerate(
            np.arange(
                tolerance_stepsize,
                max_tolerance + tolerance_stepsize,
                tolerance_stepsize,
            )
        ):
            logger.info("Checking for tolerance {:.2f} ...".format(t))
            r = alg.run(
                Nmax=Nmax,
                Nmin=Nmin,
                angles=angles,
                tolerance=t,
                distance=distance,
                vacuum=vacuum,
                no_idealize=no_idealize,
                symprec=symprec,
                angle_tolerance=angle_tolerance,
                weight=weight,
                verbosity=verbosity,
            )
            if r is not None:
                stresses = [k.stress for k in r]
                idx = stresses.index(min(stresses))
                interfaces.append(r[idx])
                break
        if len(interfaces) > 0:
            stresses = [k.stress for k in interfaces]
            idx = stresses.index(min(stresses))
            intf = interfaces[idx]
            set_verbosity_level(1)
            logger.info("Found coincidence structure: {}".format(intf))
            return intf
        else:
            logger.critical("Could not find any matching unit cells.")
            return None

    interface = circle_loop()
    atoms = interface.stack.copy()
    name = atoms.get_chemical_formula() + "_angle{:.2f}_stress{:.2f}.xyz".format(
        interface.angle, interface.stress
    )
    logger.info(f"Writing structure to {name} ...")
    atoms.write(name)


if __name__ == "__main__":
    app()
