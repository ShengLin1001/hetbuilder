import ase.io
from ase.geometry import permute_axes
from ase import neighborlist
from ase.data import covalent_radii
from ase.build import make_supercell
from ase.neighborlist import NeighborList, NewPrimitiveNeighborList

from spglib import find_primitive

import networkx as nx

import numpy as np

from collections import namedtuple

from hetbuilder.log import *


def find_fragments(atoms, scale=1.0) -> list:
    """Finds unconnected structural fragments by constructing
    the first-neighbor topology matrix and the resulting graph
    of connected vertices.

    Args:
        atoms: :class:`~ase.atoms.Atoms` or :class:`~aimstools.structuretools.structure.Structure`.
        scale: Scaling factor for covalent radii.

    Note:
        Requires networkx library.

    Returns:
        list: NamedTuple with indices and atoms object.

    """

    radii = scale * covalent_radii[atoms.get_atomic_numbers()]
    nl = NeighborList(
        radii,
        bothways=True,
        self_interaction=False,
        skin=0.0,
        primitive=NewPrimitiveNeighborList,
    )
    nl.update(atoms)
    connectivity_matrix = nl.get_connectivity_matrix(sparse=False)
    edges = np.argwhere(connectivity_matrix == 1)

    graph = nx.from_edgelist(edges)  # converting to a graph
    con_tuples = list(
        nx.connected_components(graph)
    )  # graph theory can be pretty handy
    fragments = [
        atoms[list(i)] for i in con_tuples
    ]  # the fragments are not always layers

    fragments_dict = {}
    i = 0
    for tup, atom in zip(con_tuples, fragments):
        fragment = namedtuple("fragment", ["indices", "atoms"])
        indices = []
        for entry in tup:
            indices.append(entry)
        indices = set(indices)
        fragments_dict[i] = fragment(indices, atom)
        i += 1
    fragments_dict = [
        v
        for k, v in sorted(
            fragments_dict.items(),
            key=lambda item: np.average(item[1][1].get_positions()[:, 2]),
        )
    ]
    return fragments_dict


def find_periodic_axes(atoms: "ase.atoms.Atoms") -> dict:
    """Evaluates if given structure is qualitatively periodic along certain lattice directions.

    Args:
        atoms: ase.atoms.Atoms object.

    Note:
        A criterion is a vacuum space of more than 10.0 Anström.

    Returns:
        dict: Axis : Bool pairs.
    """
    atoms = atoms.copy()
    sc = make_supercell(atoms, 2 * np.identity(3), wrap=True)
    fragments = find_fragments(sc, scale=1.5)
    crit1 = True if len(fragments) > 1 else False
    pbc = dict(zip([0, 1, 2], [True, True, True]))
    if crit1:
        for axes in (0, 1, 2):
            spans = []
            for tup in fragments:
                start = np.min(tup.atoms.get_positions()[:, axes])
                end = np.max(tup.atoms.get_positions()[:, axes])
                spans.append((start, end))
            spans = list(set(spans))
            spans = sorted(spans, key=lambda x: x[0])
            if len(spans) > 1:
                for k, l in zip(spans[:-1], spans[1:]):
                    d1 = abs(k[1] - l[0])
                    d2 = abs(
                        k[1] - l[0] - sc.cell.lengths()[axes]
                    )  # check if fragments are separated by a simple translation
                    nd = np.min([d1, d2])
                    #if nd >= 25.0:
                    if nd >= 10.0:
                        pbc[axes] = False
                        break
    return pbc


def recenter(atoms: "ase.atoms.Atoms") -> "ase.atoms.Atoms":
    """Recenters atoms to be in the unit cell, with vacuum on both sides.
    The unit cell length c is always chosen such that it is larger than a and b.

    Returns:
        atoms : modified atoms object.

    Note:
        The ase.atoms.center() method is supposed to do that, but sometimes separates the layers. I didn't find a good way to circumvene that.
    """
    # have to think about the viewing directions here
    atoms = atoms.copy()
    atoms.wrap(pretty_translation=True)
    atoms.center(axis=(2))
    mp = atoms.get_center_of_mass(scaled=False)
    cp = (atoms.cell[0] + atoms.cell[1] + atoms.cell[2]) / 2
    pos = atoms.get_positions(wrap=False)
    pos[:, 2] += np.abs((mp - cp))[2]
    for z in range(pos.shape[0]):
        lz = atoms.cell.lengths()[2]
        if pos[z, 2] >= lz:
            pos[z, 2] -= lz
        if pos[z, 2] < 0:
            pos[z, 2] += lz
    atoms.set_positions(pos)
    newcell, newpos, newscal, numbers = (
        atoms.get_cell(),
        atoms.get_positions(wrap=False),
        atoms.get_scaled_positions(wrap=False),
        atoms.numbers,
    )
    z_pos = newpos[:, 2]
    span = np.max(z_pos) - np.min(z_pos)
    newcell[0, 2] = newcell[1, 2] = newcell[2, 0] = newcell[2, 1] = 0.0
#    newcell[2, 2] = span + 100.0
    axes = [0, 1, 2]
    lengths = np.linalg.norm(newcell, axis=1)
    order = [x for x, y in sorted(zip(axes, lengths), key=lambda pair: pair[1])]
#    while True:
#        if (order == [0, 1, 2]) or (order == [1, 0, 2]):
#            break
#        newcell[2, 2] += 10.0
#        lengths = np.linalg.norm(newcell, axis=1)
#        order = [x for x, y in sorted(zip(axes, lengths), key=lambda pair: pair[1])]
    newpos = newscal @ newcell
    newpos[:, 2] = z_pos
    atoms = ase.Atoms(positions=newpos, numbers=numbers, cell=newcell, pbc=atoms.pbc)
    return atoms


def recenter_to_bottom(atoms: "ase.atoms.Atoms") -> "ase.atoms.Atoms":
    """Recenters atoms to be at the bottom of the unit cell, with vacuum on the top.

    The unit cell length c is adapted such that it accommodates all atoms comfortably at the bottom,
    leaving ample vacuum space above.

    Args:
        atoms (ase.atoms.Atoms): The atoms object to be recentered.

    Returns:
        ase.atoms.Atoms: The modified atoms object with atoms recentered to the bottom.
    """
    # First, ensure all atoms are within the unit cell boundaries.
    atoms = atoms.copy()
    atoms.wrap(pretty_translation=True)

    # Get current positions and the z-span of the atoms.
    pos = atoms.get_positions(wrap=False)
    z_min = np.min(pos[:, 2])
    z_max = np.max(pos[:, 2])
    z_span = z_max - z_min

    # Calculate the new height of the unit cell to include vacuum space above.
    # Here, we add an extra 50 units of vacuum space, but this can be adjusted as needed.
    #new_z_height = z_span + 50.0

    # Shift all atoms down to the bottom of the cell.
    pos[:, 2] -= z_min  # Shifts the bottom atom to z=0

    # Apply the new positions back to the atoms object.
    atoms.set_positions(pos)

    # Now, update the cell dimensions, specifically the z-axis to accommodate the new height.
    newcell = atoms.cell.copy()
    #newcell[2, 2] = new_z_height
    atoms.set_cell(newcell, scale_atoms=False)

    return atoms




def check_if_2d(atoms: "ase.atoms.Atoms") -> bool:
    """Evaluates if structure is qualitatively two-dimensional.

    Note:
        A structure is considered 2D if only one axis is non-periodic.

    Returns:
        bool: 2D or not to 2D, that is the question.
    """
    pbcax = find_periodic_axes(atoms)
    if sum(list(pbcax.values())) == 2:
        return True
    else:
        return False


def check_if_primitive(atoms: "ase.atoms.Atoms") -> None:
    """ Checks if input configuration is primitive via spglib.
    
    A warning is raised if not.

    """
    cell = (atoms.cell, atoms.get_scaled_positions(), atoms.numbers)
    lattice, scaled_positions, numbers = find_primitive(cell, symprec=1e-5)
    is_primitive = (np.abs(lattice - atoms.cell) < 1e-4).all()
    if not is_primitive:
        logger.warning("It seems that the structure {} is not primitive.".format(atoms))
        logger.warning("This might lead to unexpected results.")


def check_atoms(atoms: "ase.atoms.Atoms") -> "ase.atoms.Atoms":
    """ Runs a series of checks on the input configuration.

    This should assert that the input atoms are 2d, oriented in the xy plane, and centered in the middle of the unit cell.

    """
    cell = atoms.cell.copy()
    zerovecs = np.where(~cell.any(axis=1))[0]
    is_2d = False
    is_3d = False
    if len(zerovecs) == 3:
        logger.warning("You cannot specify 0D molecules as structure input.")
    elif len(zerovecs) == 2:
        logger.warning("You cannot specify 1D chains as structure input.")
    elif len(zerovecs) == 1:
        is_2d = True
    elif len(zerovecs) == 0:
        is_3d = True

    atoms.cell = atoms.cell.complete()
    check_if_primitive(atoms)

    # check that cell is oriented in xy
    if is_2d:
        non_pbc_axis = zerovecs[0]
        if non_pbc_axis != 2:
            old = list(set([0, 1, 2]) - set([non_pbc_axis]))
            new = old + [non_pbc_axis]
            atoms = permute_axes(atoms, new)
        atoms = recenter(atoms)

    # more expensive checks to see if structure is suitably 2d
    if is_3d:
        is_2d = check_if_2d(atoms)
        if not is_2d:
            logger.error(
                "It seems that the structure {} is not two-dimensional.".format(atoms)
            )
            logger.error(
                "Consider setting one of the lattice vectors to zero or to a suitably large value."
            )
            raise Exception("Structure does not appear to be 2d.")
        else:
            atoms = recenter(atoms)

    return atoms

