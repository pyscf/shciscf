#!/usr/bin/env python
# Copyright 2014-2018 The PySCF Developers. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy
import scipy

from pyscf import __config__

__config__.shci_SHCIEXE = "shci_emulator"
__config__.shci_SHCISCRATCHDIR = "."
from functools import reduce
from pyscf import gto, scf, mcscf
from pyscf.shciscf import shci

# Test whether SHCI executable can be found. If it can, trigger tests that
# require it.
NO_SHCI = True
if shci.settings.SHCIEXE != "shci_emulator" and shci.settings.SHCIEXE != None:
    print("Found SHCI =>", shci.settings.SHCIEXE)
    NO_SHCI = False
else:
    print("No SHCI found")


def make_o2():
    b = 1.208
    mol = gto.Mole()
    mol.build(
        verbose=0,
        output=None,
        atom="O 0 0 %f; O 0 0 %f" % (-b / 2, b / 2),
        basis="ccpvdz",
        symmetry=True,
    )

    # Create HF molecule
    mf = scf.RHF(mol)
    mf.conv_tol = 1e-9
    return mf.run()


def D2htoDinfh(SHCI, norb, nelec):
    from pyscf import symm

    coeffs = numpy.zeros(shape=(norb, norb)).astype(complex)
    nRows = numpy.zeros(shape=(norb,), dtype=int)
    rowIndex = numpy.zeros(shape=(2 * norb,), dtype=int)
    rowCoeffs = numpy.zeros(shape=(2 * norb,), dtype=float)

    i, orbsym1, ncore = 0, [0] * len(SHCI.orbsym), len(SHCI.orbsym) - norb

    while i < norb:
        symbol = symm.basis.linearmole_irrep_id2symb(
            SHCI.groupname, SHCI.orbsym[i + ncore]
        )
        if symbol[0] == "A":
            coeffs[i, i] = 1.0
            orbsym1[i] = 1
            nRows[i] = 1
            rowIndex[2 * i] = i
            rowCoeffs[2 * i] = 1.0
            if len(symbol) == 3 and symbol[2] == "u":
                orbsym1[i] = 2
        else:
            if i == norb - 1:
                print("the orbitals dont have dinfh symmetry")
                exit(0)
            l = int(symbol[1])
            orbsym1[i], orbsym1[i + 1] = 2 * l + 3, -(2 * l + 3)
            if len(symbol) == 4 and symbol[2] == "u":
                orbsym1[i], orbsym1[i + 1] = orbsym1[i] + 1, orbsym1[i + 1] - 1
            if symbol[3] == "x":
                m1, m2 = 1.0, -1.0
            else:
                m1, m2 = -1.0, 1.0

            nRows[i] = 2
            if m1 > 0:
                coeffs[i, i], coeffs[i, i + 1] = ((-1) ** l) * 1.0 / (2.0 ** 0.5), (
                    (-1) ** l
                ) * 1.0j / (2.0 ** 0.5)
                rowIndex[2 * i], rowIndex[2 * i + 1] = i, i + 1
            else:
                coeffs[i, i + 1], coeffs[i, i] = ((-1) ** l) * 1.0 / (2.0 ** 0.5), (
                    (-1) ** l
                ) * 1.0j / (2.0 ** 0.5)
                rowIndex[2 * i], rowIndex[2 * i + 1] = i + 1, i

            rowCoeffs[2 * i], rowCoeffs[2 * i + 1] = ((-1) ** l) * 1.0 / (2.0 ** 0.5), (
                (-1) ** l
            ) * 1.0 / (2.0 ** 0.5)
            i = i + 1

            nRows[i] = 2
            if m1 > 0:  # m2 is the complex number
                rowIndex[2 * i] = i - 1
                rowIndex[2 * i + 1] = i
                rowCoeffs[2 * i], rowCoeffs[2 * i + 1] = 1.0 / (2.0 ** 0.5), -1.0 / (
                    2.0 ** 0.5
                )
                coeffs[i, i - 1], coeffs[i, i] = 1.0 / (2.0 ** 0.5), -1.0j / (
                    2.0 ** 0.5
                )
            else:
                rowIndex[2 * i] = i
                rowIndex[2 * i + 1] = i - 1
                rowCoeffs[2 * i], rowCoeffs[2 * i + 1] = 1.0 / (2.0 ** 0.5), -1.0 / (
                    2.0 ** 0.5
                )
                coeffs[i, i], coeffs[i, i - 1] = 1.0 / (2.0 ** 0.5), -1.0j / (
                    2.0 ** 0.5
                )

        i = i + 1

    return coeffs, nRows, rowIndex, rowCoeffs, orbsym1


def DinfhtoD2h(SHCI, norb, nelec):
    from pyscf import symm

    nRows = numpy.zeros(shape=(norb,), dtype=int)
    rowIndex = numpy.zeros(shape=(2 * norb,), dtype=int)
    rowCoeffs = numpy.zeros(shape=(4 * norb,), dtype=float)

    i, ncore = 0, len(SHCI.orbsym) - norb

    while i < norb:
        symbol = symm.basis.linearmole_irrep_id2symb(
            SHCI.groupname, SHCI.orbsym[i + ncore]
        )
        if symbol[0] == "A":
            nRows[i] = 1
            rowIndex[2 * i] = i
            rowCoeffs[4 * i] = 1.0
        else:
            l = int(symbol[1])

            if symbol[3] == "x":
                m1, m2 = 1.0, -1.0
            else:
                m1, m2 = -1.0, 1.0

            nRows[i] = 2
            rowIndex[2 * i], rowIndex[2 * i + 1] = i, i + 1
            if m1 > 0:
                rowCoeffs[4 * i], rowCoeffs[4 * i + 2] = ((-1) ** l) * 1.0 / (
                    2.0 ** 0.5
                ), 1.0 / (2.0 ** 0.5)
            else:
                rowCoeffs[4 * i + 1], rowCoeffs[4 * i + 3] = -((-1) ** l) * 1.0 / (
                    2.0 ** 0.5
                ), 1.0 / (2.0 ** 0.5)

            i = i + 1

            nRows[i] = 2
            rowIndex[2 * i], rowIndex[2 * i + 1] = i - 1, i
            if m1 > 0:  # m2 is the complex number
                rowCoeffs[4 * i + 1], rowCoeffs[4 * i + 3] = -((-1) ** l) * 1.0 / (
                    2.0 ** 0.5
                ), 1.0 / (2.0 ** 0.5)
            else:
                rowCoeffs[4 * i], rowCoeffs[4 * i + 2] = ((-1) ** l) * 1.0 / (
                    2.0 ** 0.5
                ), 1.0 / (2.0 ** 0.5)

        i = i + 1

    return nRows, rowIndex, rowCoeffs


class KnownValues(unittest.TestCase):
    @unittest.skipIf(NO_SHCI, "No SHCI Settings Found")
    def test_SHCI_CASCI(self):
        """
        Compare SHCI-CASCI calculation to CASCI calculation.
        """
        mf = make_o2()
        # Number of orbital and electrons
        ncas = 8
        nelecas = 12

        mc = mcscf.CASCI(mf, ncas, nelecas)
        e_casscf = mc.kernel()[0]
        mc = mcscf.CASCI(mf, ncas, nelecas)
        mc.fcisolver = shci.SHCI(mf.mol)
        mc.fcisolver.stochastic = True
        mc.fcisolver.nPTiter = 0  # Turn off perturbative calc.
        mc.fcisolver.sweep_iter = [0]
        mc.fcisolver.sweep_epsilon = [1e-12]
        e_shciscf = mc.kernel()[0]
        self.assertAlmostEqual(e_shciscf, e_casscf, places=6)
        mc.fcisolver.cleanup_dice_files()

    @unittest.skipIf(NO_SHCI, "No SHCI Settings Found")
    def test_SHCISCF_CASSCF(self):
        """
        Compare SHCI-CASSCF calculation to CASSCF calculation.
        """
        mf = make_o2()
        # Number of orbital and electrons
        ncas = 8
        nelecas = 12

        mc = mcscf.CASSCF(mf, ncas, nelecas)
        e_casscf = mc.kernel()[0]

        mc = shci.SHCISCF(mf, ncas, nelecas)
        mc.fcisolver.stochastic = True
        mc.fcisolver.nPTiter = 0  # Turn off perturbative calc.
        mc.fcisolver.sweep_iter = [0]
        mc.fcisolver.sweep_epsilon = [1e-12]
        e_shciscf = mc.kernel()[0]
        self.assertAlmostEqual(e_shciscf, e_casscf, places=6)
        mc.fcisolver.cleanup_dice_files()

    @unittest.skipIf(NO_SHCI, "No SHCI Settings Found")
    def test_spin_1RDM(self):
        mol = gto.M(
            atom="""
            C   0.0000     0.0000    0.0000  
            H   -0.9869    0.3895    0.2153  
            H   0.8191     0.6798   -0.1969  
            H   0.1676    -1.0693   -0.0190  
        """,
            spin=1,
        )
        ncas, nelecas = (7, 7)
        mf = scf.ROHF(mol).run()
        mc = shci.SHCISCF(mf, ncas, nelecas)
        mc.davidsonTol = 1e-8
        mc.dE = 1e-12
        mc.kernel()

        #
        # Get our spin 1-RDMs
        #
        dm1 = mc.fcisolver.make_rdm1(0, ncas, nelecas)
        dm_ab = mc.fcisolver.make_rdm1s()  # in MOs
        dm1_check = numpy.linalg.norm(dm1 - numpy.sum(dm_ab, axis=0))
        self.assertLess(dm1_check, 1e-5)

    @unittest.skipIf(NO_SHCI, "No SHCI Settings Found")
    def test_spin_RDMs(self):
        mol = gto.M(
            atom="""
            C   0.0000     0.0000    0.0000  
            H   -0.9869    0.3895    0.2153  
            H   0.8191     0.6798   -0.1969  
            H   0.1676    -1.0693   -0.0190  
        """,
            spin=1,
        )
        ncas, nelecas = (7, 7)
        mf = scf.ROHF(mol).run()
        mc = shci.SHCISCF(mf, ncas, nelecas)
        mc.davidsonTol = 1e-8
        mc.dE = 1e-12
        mc.fcisolver.DoRDM = True
        mc.fcisolver.DoSpinRDM = True
        mc.kernel()
        
        #
        # Get partial 1-RDM and 2-RDM as references
        #
        onepdm, twopdm = mc.fcisolver.make_rdm12(0, ncas, mc.nelecas)

        #
        # Get our spin 1-RDMs and 2-RDMs
        #
        (dm1a, dm1b), (dm2aa, dm2ab, dm2bb) = mc.fcisolver.make_rdm12s(ncas, mc.nelecas)
        oneRDM = dm1a + dm1b
        twoRDM = dm2aa + dm2ab + dm2ab.transpose(2,3,0,1) + dm2bb
        self.assertLess(numpy.linalg.norm(oneRDM - onepdm), 5e-5)
        self.assertLess(numpy.linalg.norm(twopdm - twoRDM), 5e-5)
        
    @unittest.skipIf(NO_SHCI, "No SHCI Settings Found")
    def test_DFCASCI_natorb(self):
        #
        mol = gto.M(atom="C 0 0 0; C 0 0 1;", basis="ccpvdz", spin=2, verbose=0)
        mf = scf.RHF(mol).density_fit().run()
        ncas, nelecas = (8, 12)
        mc = mcscf.CASCI(mf, ncas, nelecas).density_fit()
        mc.fcisolver = shci.SHCI(mf.mol)
        mc.natorb = True
        mc.kernel()

        mc.make_rdm1()
        no_coeff = mc.mo_coeff
        dm1_no = reduce(
            numpy.dot,
            (no_coeff.conj().T, mf.get_ovlp(), mc.make_rdm1(), mf.get_ovlp(), no_coeff),
        )
        numpy.testing.assert_allclose(
            dm1_no.diagonal(), mc.mo_occ, rtol=3e-4, atol=1e-5
        )

    def test_D2htoDinfh(self):
        SHCI = lambda: None
        SHCI.groupname = "Dooh"
        # SHCI.orbsym = numpy.array([15,14,0,6,7,2,3,10,11,15,14,17,16,5,13,12,16,17,12,13])
        SHCI.orbsym = numpy.array(
            [15, 14, 0, 7, 6, 2, 3, 10, 11, 15, 14, 17, 16, 5, 12, 13, 17, 16, 12, 13]
        )

        coeffs, nRows, rowIndex, rowCoeffs, orbsym = D2htoDinfh(SHCI, 20, 20)
        coeffs1, nRows1, rowIndex1, rowCoeffs1, orbsym1 = shci.D2htoDinfh(SHCI, 20, 20)
        self.assertTrue(numpy.array_equal(coeffs1, coeffs))
        self.assertTrue(numpy.array_equal(nRows1, nRows))
        self.assertTrue(numpy.array_equal(rowIndex1, rowIndex))
        self.assertTrue(numpy.array_equal(rowCoeffs1, rowCoeffs))
        self.assertTrue(numpy.array_equal(orbsym1, orbsym))

    def test_DinfhtoD2h(self):
        SHCI = lambda: None
        SHCI.groupname = "Dooh"
        # SHCI.orbsym = numpy.array([15,14,0,6,7,2,3,10,11,15,14,17,16,5,13,12,16,17,12,13])
        SHCI.orbsym = numpy.array(
            [15, 14, 0, 7, 6, 2, 3, 10, 11, 15, 14, 17, 16, 5, 12, 13, 17, 16, 12, 13]
        )

        nRows, rowIndex, rowCoeffs = DinfhtoD2h(SHCI, 20, 20)
        nRows1, rowIndex1, rowCoeffs1 = shci.DinfhtoD2h(SHCI, 20, 20)
        self.assertTrue(numpy.array_equal(nRows1, nRows))
        self.assertTrue(numpy.array_equal(rowIndex1, rowIndex))
        self.assertTrue(numpy.array_equal(rowCoeffs1, rowCoeffs))


if __name__ == "__main__":
    print("Tests for shciscf interface")
    unittest.main()
