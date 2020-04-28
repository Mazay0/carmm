def analyse_all_bonds(model, verbose=True):
    '''
    Returns a table of bond distance analysis for the supplied model.
    TODO: - Setup method to return information
          - Setup routine functionality to use analyse_bonds

    Parameters:

    model: Atoms object or string. If string it will read a file
    in the same folder, e.g. "name.traj"
    verbose: Boolean
    Determines whether the output should be printed to screen
    '''
    import numpy as np
    # Combination as AB = BA for bonds, avoiding redundancy
    from itertools import combinations_with_replacement

    # Read file or Atoms object
    if isinstance(model, str) is True:
        from ase.io import read
        model = read(model)

    from ase.geometry.analysis import Analysis
    analysis = Analysis(model)
    dash = "-" * 40

    # set() to ensure unique chemical symbols list
    list_of_symbols = list(set(model.get_chemical_symbols()))
    all_bonds = combinations_with_replacement(list_of_symbols, 2)

    # Table heading
    if verbose:
        print(dash)
        print('{:<6.5s}{:<6.5s}{:>4.10s}{:^13.10s}{:>4.10s}'.format(
            "Bond", "Count", "Average", "Minimum", "Maximum"))
        print(dash)

    # Iterate over all arrangements of chemical symbols
    for bonds in all_bonds:
        AB_Bonds, AB_BondsValues = analyse_bonds(model, bonds[0], bonds[1], verbose=False)

        print_AB = bonds[0]+'-'+bonds[1]
        #AB_Bonds = analysis.get_bonds(A, B)

        # Make sure bond exist before retrieving values, then print contents
        if verbose and AB_BondsValues is not None:
            #AB_BondsValues = analysis.get_values(AB_Bonds)
            print('{:<8.8s}{:<6.0f}{:>4.6f}{:^12.6f}{:>4.6f}'.format(
                print_AB, len(AB_BondsValues[0]), np.average(AB_BondsValues),
                np.amin(AB_BondsValues), np.amax(AB_BondsValues)))

def analyse_bonds(model, A, B, verbose=True):
    '''
    Check A-B distances present in the model.
        model: Atoms object or string. If string it will read a file
        in the same folder, e.g. "name.traj"
    TODO: Setup method to return information

    Parameters:
    A: string, chemical symbol, e.g. "H"
    B: string, chemical symbol, e.g. "H"
    verbose: Boolean
        Whether to print information to screen
    '''

    # Read file or Atoms object
    if isinstance(model, str) is True:
        from ase.io import read
        model = read(model)

    from ase.geometry.analysis import Analysis
    analysis = Analysis(model)
    dash = "-" * 40
    print_AB = A + "-" + B
    # Retrieve bonds and values
    AB_Bonds = analysis.get_bonds(A, B)
    if AB_Bonds == [[]]:
        AB_BondsValues = None
    else:
        AB_BondsValues = analysis.get_values(AB_Bonds)

    if verbose and AB_BondsValues is not None:
        # Table header
        print(dash)
        print(print_AB+"       Distance / Angstrom")
        print(dash)
        print('{:<6.5s}{:>4.10s}{:^13.10s}{:>4.10s}'.format(
            "count", "average", "minimum", "maximum"))
        # Table contents
        import numpy as np
        print('{:<6.0f}{:>4.6f}{:^12.6f}{:>4.6f}'.format(
            len(AB_BondsValues[0]), np.average(AB_BondsValues),
            np.amin(AB_BondsValues), np.amax(AB_BondsValues)))

    return AB_Bonds, AB_BondsValues

def search_abnormal_bonds(model, verbose=True):
    '''
    Check all bond lengths in the model for abnormally
    short ones, ie. less than 0.74 Angstrom.

    Parameters:
    model: Atoms object or string. If string it will read a file
        in the same folder, e.g. "name.traj"
    '''

    # Combination as AB = BA for bonds, avoiding redundancy
    from itertools import combinations_with_replacement
    # Imports necessary to work out accurate minimum bond distances
    from ase.data import chemical_symbols, covalent_radii

    # Read file or Atoms object
    if isinstance(model, str) is True:
        from ase.io import read
        model = read(model)

    # Define lists of variables
    abnormal_bonds = []
    list_of_abnormal_bonds = []

    from ase.geometry.analysis import Analysis
    analysis = Analysis(model)
    # set() to ensure unique chemical symbols list
    list_of_symbols = list(set(model.get_chemical_symbols()))
    all_bonds = combinations_with_replacement(list_of_symbols, 2)

    # Iterate over all arrangements of chemical symbols
    for bonds in all_bonds:
        A = bonds[0]
        B = bonds[1]
        # For softcoded bond cutoff
        sum_of_covalent_radii = covalent_radii[chemical_symbols.index(A)]+covalent_radii[chemical_symbols.index(B)]

        print_AB = A+'-'+B
        AB_Bonds = analysis.get_bonds(A, B)
        # With the exception of the sum of covalent radii, everything up to here is identical to
        # analyse_all_bonds
        # TODO: Combine with functionality for analyse_all_bonds so the duplication is removed.

        # Make sure bond exist before retrieving values
        if not AB_Bonds == [[]]:
            AB_BondsValues = analysis.get_values(AB_Bonds)

            for i in range(0, len(AB_BondsValues)):
                for values in AB_BondsValues[i]:
                    # TODO: move the 75% of sum_of_covalent_radii before the loops
                    if values < max(0.4, sum_of_covalent_radii*0.75):
                        abnormal_bonds += [1]
                        list_of_abnormal_bonds = list_of_abnormal_bonds + [print_AB]

    # Abnormality check
    # is it possible to make a loop with different possible values instead of 0.75 and takes the average
    if len(abnormal_bonds) > 0:
        if verbose:
            print("A total of", len(abnormal_bonds),
            "abnormal bond lengths observed (<" + str(max(0.4, sum_of_covalent_radii*0.75)) + " A).")
            print("Identities:", list_of_abnormal_bonds)
        return False
    else:
        if verbose:
            print("OK")
        return True

def compare_structures(atoms1, atoms2, label=None):
    '''

    Comparison of two input structures to identify equivalent atoms but incorrect index ordering

    Parameters:

    atoms1: Atoms object or trajectory of individual atoms
        An atoms object
    atoms2: Atoms object or trajectory of individual atoms
        Another atoms object
    label: String of elemental character
        Only necessary to limit search to specific atomic species
    '''
    from math import sqrt

    if len(atoms1) != len(atoms2):
        print("The inputs don't contain the same number of atoms.")
        exit()

    # Configure arrays
    differences = []
    atoms2_indices = []
    # Iterate over indices of all atoms in structure 1 and compare to structure 2.
    for i in range(len(atoms1.positions)):
        xyz = atoms1.positions[i]
        distance_sq = 999999.9
        temp_index = 0
        for j in range(len(atoms2.positions)):
            if atoms1.symbols[i] == atoms2.symbols[j] and (atoms1.symbols[i] == label or label == None):
                temp_distance_sq = ((atoms2.positions[j][0] - xyz[0]) * (atoms2.positions[j][0] - xyz[0])
                                    + (atoms2.positions[j][1] - xyz[1]) * (atoms2.positions[j][1] - xyz[1])
                                    + (atoms2.positions[j][2] - xyz[2]) * (atoms2.positions[j][2] - xyz[2]))

                if distance_sq > temp_distance_sq:
                    distance_sq = temp_distance_sq
                    temp_index = j

        atoms2_indices.append(temp_index)
        differences.append(sqrt(distance_sq))

    return atoms2_indices, differences

def get_indices_of_elements(list_of_symbols, symbol):
    '''

    Check an atoms object for occurences of symbols given and return indices

    Parameters:

    list_of_symbols: List of strings
        Symbols from an atoms object in structural order
    symbol:
        Symbol to search for
    '''
    return [i for i, x in enumerate(list_of_symbols) if x == symbol.capitalize()]
