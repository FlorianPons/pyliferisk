#!/usr/bin/python
# -*- coding: utf-8 -*-
#    pyrisk: A python library for simple actuarial calculations
#    Version: 1.8 - March 2017
#    Copyright (C) 2017 Francisco Garate, Florian Pons
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Mortality table class ----------------

# This class represente one mortality table
# with basic actuarial values calculated (for optimisations)
class MortalityTable:
    def __init__(self, l_x=[], q_x=[], nt=None, perc=100):
        self.l_x = l_x
        self.q_x = q_x
        self.e_x = []
        self.perc = perc
        self.nt = nt
        self.w = 0

        # for retrocompatibility
        if nt:
            mt = nt
            init = mt[0]
            self.q_x = [0.0] * init
            end_val = 0
            for val in mt[1:]:
                if end_val < 1000.0:
                    end_val = val * perc / 100
                    self.q_x.append(end_val)
            if perc != 100:
                self.q_x.append(1000)

        # Actuarial notation -------------------
        # if l_x is empty, assume qx is known
        if self.l_x == []:
            self.l_x = [100000.0]
            for val in self.q_x:
                self.l_x.append(self.l_x[-1] * (1 - val / 1000))
        if self.l_x[-1] != 0.0:
            self.l_x.append(0.0)
        if self.w == 0:
            self.w = self.l_x.index(0) - 1


class Pers:
    """represent a group of persone who disappear on first death,
    can be one persone only
    MortalityTable_list: list of MortalityTable.
    On MortalityTable for one persone
    (can be only MortalityTable object if one persone)
    age_list: used to calculate relative offset of tables,
    relevante only if more than one persone"""
    def __init__(self, MortalityTable_list, age_list=[0]):
        self.l_x = []
        self.q_x = []
        self.e_x = []
        self.w = 0

        if type(MortalityTable_list) != list:
            MortalityTable_list = [MortalityTable_list]
        # calculate offsets
        age_min = min(age_list)
        offsets = [x-age_min for x in age_list]

        # Actuarial notation -------------------
        for i in range(len(MortalityTable_list)):
            mt = MortalityTable_list[i]
            os = offsets[i]
            if self.w == 0:
                self.w = mt.w-os
            else:
                self.w = min(self.w, mt.w-os)

        # calculate l_x
        self.l_x = MortalityTable_list[0].l_x[offsets[0]:]
        for t in range(1, len(MortalityTable_list)):
            mt = MortalityTable_list[t]
            os = offsets[t]
        for i in range(0, self.w):
            if i < len(self.l_x):
                self.l_x.append(0)
            if i+os < len(mt.l_x):
                self.l_x[i] *= mt.l_x[i+os]
            else:
                self.l_x[i] = 0

        # calculate q_x
        if len(self.l_x) > 0:
            lx = self.l_x[0]
        for lx1 in self.l_x[1:]:
            if lx > 0:
                self.q_x.append((lx - lx1) * 1000 / lx)
            else:
                self.q_x.append(1)
            lx = lx1

        # calculate e_x
        sum_lx = sum(self.l_x[0:-1])
        for g in range(0, len(self.l_x) - 1):
            lx_g = self.l_x[g]
            sum_lx = sum_lx - lx_g
            if lx_g > 0:
                self.e_x.append(0.5 + sum_lx / lx_g)
                # [g+1:-2] according notes from ucm.es, [g+1:-1]
            else:
                self.e_x.append(0.5)

    # Actuarial notation -------------------
    def qx(self, x):
        """ qx: Returns the probability that a life aged x dies before 1 year
                With the convention: the true probability is qx/1000
        Args:
            self: the mortality table
            x: the age as integer number.
        """
        if x < len(self.q_x):
            return self.q_x[x]
        else:
            return 0

    def lx(self, x):
        """ lx : Returns the number of survivors at begining of age x """
        if x < len(self.l_x):
            return self.l_x[x]
        else:
            return 0

    def w(self):
        """ w : ultimate age (lw = 0) """
        return len(self.l_x)

    def dx(self, x):
        """ Returns the number of dying at begining of age x """
        end_x_val = self.l_x.index(0)
        if x < end_x_val:
            return self.l_x[x] - self.l_x[x + 1]
        else:
            return 0.0

    def px(self, x):
        """ px : Returns the probability of surviving within 1 year """
        return 1000 - self.qx(x)

    def tpx(self, x, t):
        """ tqx : Returns the probability
            that x will survive within t years """
        """ npx : Returns n years survival probability at age x """
        return self.l_x[x + t] / self.l_x[x]

    def tqx(self, x, t):
        """ nqx : Returns the probability to die within n years at age x """
        return 1 - self.l_x[x + t] / self.l_x[x]

    def tqxn(self, x, n, t):
        """ n/qx : Probability to die in n years being alive at age x.
        Probability that x survives n year,
        and then dies in th subsequent t years """
        return self.tpx(x, t) * self.qx(x + n)

    def ex(self, x):
        """ ex : Returns the curtate expectation of life. Life expectancy """
        if x < len(self.e_x):
            return self.e_x[x]
        else:
            return 0

    def mx(self, x):
        """ mx : Returns the central mortality rate """
        return self.dx(x) / self.l_x[x]


# Actuarial class: calculate actuarial notations

class Actuarial(Pers):
    # rate: actuarial rate
    # pers: MortalityTable representing one persone
    def __init__(self, rate, pers):
        if type(rate) is float:
            self.rate = lambda age: rate
        else:
            self.rate = rate
        self.l_x = pers.l_x
        self.q_x = pers.q_x
        self.e_x = pers.e_x
        self.w = pers.w

        # Commutations ------------------

        # Dx calculation
        self.D_x = []
        age = 0
        for j in self.l_x:
            i = self.rate(age)
            self.D_x.append(((1 / (1 + i)) ** age) * j)
            age += 1

        # Nx calculation
        self.N_x = []
        for k in range(0, len(self.D_x)):
            self.N_x.append(sum(self.D_x[k:]))
            # [m:-2] according notes from ucm.es, [m:-1]

        # Cx calculation
        self.C_x = []
        age = -1
        if len(self.l_x) > 0:
            lx0 = self.l_x[0]
        for lx1 in self.l_x:   # [:-1]
            age += 1
            i = self.rate(age)
            Cx = ((1/(1+i))**(age+1))*(lx0-lx1)*((1+i)**0.5)
            self.C_x.append(Cx)
            lx0 = lx1

        # Mx calculation
        self.M_x = []
        for m in range(0, len(self.C_x)):
            self.M_x.append(sum(self.C_x[m:]))
            # [m:-2] according notes from ucm.es, [m:-1]

    # Commutations ------------------

    def Dx(self, x):
        """ Return the Dx """
        if x < len(self.D_x):
            return self.D_x[x]
        else:
            return 0

    def Nx(self, x):
        """ Return the Nx """
        if x < len(self.N_x):
            return self.N_x[x]
        else:
            return 0

    def Sx(self, x):
        """ Return the Sx """
        return sum(self.N_x[x:])

    def Cx(self, x):
        """ Return the Cx """
        if x < len(self.C_x):
            return self.C_x[x]
        else:
            return 0

    def Mx(self, x):
        """ Return the Mx """
        if x < len(self.M_x):
            return self.M_x[x]
        else:
            return 0

    def Rx(self, x):
        """ Return the Rx """
        return sum(self.M_x[x:])

    # Pure endowment: Deferred capital ---
    def nEx(self, x, n):
        """ nEx : Returns the EPV of a pure endowment (deferred capital).
        Pure endowment benefits are conditional on
        the survival of the policyholder. (v^n * npx) """
        return self.Dx(x+n)/self.Dx(x)

    # Actuarial present value

    # Whole life insurance ---
    def Ax(self, x):
        """ Ax : Returns the Expected Present Value
        (EPV) of a whole life insurance (i.e. net single premium).
        It is also commonly referred to as the
        Actuarial Value or Actuarial Present Value. """
        return self.Mx(x)/self.Dx(x)

    # Term insurance ---
    def Axn(self, x, n):
        """ (A^1)x:n : Returns the EPV (net single premium)
        of a term insurance. """
        return (self.Mx(x)-self.Mx(x+n))/self.Dx(x)

    # Deferred insurance benefits ---
    def tAx(self, x, t):
        """ n/Ax : Returns the EPV (net single premium)
        of a deferred whole life insurance. """
        return self.Mx(x+t)/self.Dx(x)

    def tAxn(self, x, n, t):
        pass

    # Endowment insurance ---
    def AExn(self, x, n):
        """ AExn : Returns the EPV of a endowment insurance.
        An endowment insurance provides a combination of
        a term insurance and a pure endowment """
        return self.Axn(x, n) + self.nEx(x, n)

    # IAx  ---

    def IAx(self, x):
        """ This function evaluates the APV of an increasing life insurance."""
        pass

    def IAxn(self, x, n):
        """ This function evaluates the APV of an increasing life insurance."""
        pass

    def qAx(self, x, q, m=1):
        """ This function evaluates the APV of
        a geometrically increasing annual annuity-due """
        pass

    def qAxn(self, x, n, q, m=1):
        pass

    def qtAx(self, x, t, q):
        pass

    def qtAxn(self, x, t, q):
        pass

    # Discrete Life Annuities ------------------

    def aaxn(self, x, n, m=1):
        """ äxn : Return the actuarial present value of
        a (immediate) temporal (term certain) annuity:
            n-year temporary life annuity-anticipatory.
            Payable 'm' per year at the beginning of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = (self.Nx(x)-self.Nx(x+n))/Dx
        else:
            res = 1
        if m == 1:
            return res
        else:
            return res - ((float(m-1)/float(m*2)) * (1 - self.nEx(x, n)))

    def axn(self, x, n, m=1):
        """ axn : Return the actuarial present value of a (immediate)
        temporal (term certain)
        annuity: n-year temporary life annuity-late.
        Payable 'm' per year at the ends of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = (self.Nx(x+1)-self.Nx(x+n+1))/Dx
        else:
            res = 0
        if m == 1:
            return res
        else:
            return res + ((float(m-1)/float(m*2)) * (1 - self.nEx(x, n)))

    def aax(self, x, m=1):
        """ äx : Returns the actuarial present value of an (immediate)
        annuity of 1 per time period (whole life annuity-anticipatory).
        Payable 'm' per year at the beginning of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = self.Nx(x)/Dx
        else:
            res = 1
        if m == 1:
            return res
        else:
            return res - (float(m-1)/float(m*2))

    def ax(self, x, m=1):
        """ ax : Returns the actuarial present value of an (immediate)
        annuity of 1 per time period (whole life annuity-late).
        Payable 'm' per year at the ends of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = self.Nx(x+1)/Dx
        else:
            res = 0
        if m == 1:
            return res
        else:
            return res + (float(m-1)/float(m*2))

    def taaxn(self, x, n, m=1):
        pass

    def taxn(self, x, n, m=1):
        pass

    def taax(self, x, t, m=1):
        """ n/äx : Return the actuarial present value of a deferred annuity
        (deferred t years): t-year deferred whole life annuity-anticipatory.
        Payable 'm' per year at the beginning of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = self.Nx(x+t)/Dx
        else:
            res = (1 if t == 0 else 0)
        if m == 1:
            return res
        else:
            return res - ((float(m-1)/float(m*2)) * (1 - self.nEx(x, t)))

    def tax(self, x, t, m=1):
        """ n/ax : Return the actuarial present value of a
        deferred annuity (deferred t years): t-year deferred whole life
        annuity-late.
        Payable 'm' per year at the ends of the period """
        Dx = self.Dx(x)
        if Dx > 0:
            res = self.Nx(x+t+1)/Dx
        else:
            res = 0
        if m == 1:
            return res
        else:
            return res + ((float(m-1)/float(m*2)) * (1 - self.nEx(x, t)))

    # Arithmetically increasing annuities (unitary) -----------------

    def Iaaxn(self, x, n):
        """ during a term certain, IAn """
        return (self.Sx(x)-self.Sx(x+n)-n*self.N_x[x+n]) / self.Dx(x)

    def Iaxn(self, x, n):
        """ during a term certain, IAn """
        return (self.Sx(x+1)-self.Sx(x+n+1)-n*self.N_x(x+n+1))/self.Dx(x)

    def Iaax(self, x):
        """ (Iä)x : Returns the present value of annuity-certain at
        the beginning of the first year and increasing linerly.
        Arithmetically increasing annuity-anticipatory """
        return self.Sx(x)/self.Dx(x)

    def Iax(self, x):
        """ (Ia)x : Returns the present value of annuity-certain at
        the end of the first year and increasing linerly.
        Arithmetically increasing annuity-late """
        return self.Sx(x+1)/self.Dx(x)

    def Iaaxn(self, x, n):
        pass

    def Iaxn(self, x, n):
        pass

    def Itaax(self, x, t):
        """ deffered t years """
        return (self.Sx(x)-self.Sx(x+t))/self.Dx(x)

    def Itax(self, x, t):
        """ deffered t years """
        return (self.Sx(x+1) - self.Sx(x+t+1))/self.Dx(x)

# Annuity formula ------------


def annuity(mt, i, x, n, p, m=1, *args):
    # annuity(mt,x,n,0/1,m=1,['a'/'g',q],-d)
    l = len(args)
    post = False
    incr = False
    deff = False
    arit = False
    wh_l = False

    if isinstance(n, str) or n == 99:
        wh_l = True
    else:
        pass

    if isinstance(m, int) and m >= 0 and l == 0:
        pass
    elif l == 0 and isinstance(m, list):
        args = (m,)
        m = 1
        incr = True
    elif l == 0 and int(m) < 0:
        args = False
        deff = True
        t = int(m) * -1
        m = 1
    elif l == 1:
        if isinstance(args[0], list):
            incr = True
        elif isinstance(args[0], int):
            if isinstance(m, list):
                deff = True
                incr = True
                t = int(args[0]) * -1
                args = (m,)
                m = 1
            else:
                deff = True
                t = int(args[0]) * -1
                args = False
        else:
            pass
    elif l == 2:
        if isinstance(args[0], list):
            deff = True
            t = int(args[1]) * -1
            incr = True
        elif isinstance(args[0], int):
            deff = True
            t = int(args[0]) * -1
            args = args[1]
        else:
            pass
    else:
        pass

    if p == 1:
        post = True
    elif p == 0:
        pass
    else:
        print('Error: payment value is 0 or 1')

    if incr:
        if 'a' in args[0]:
            arit = True
            incr = False
        elif 'g' in args[0]:
            incr = True
            q = args[0][1]
        else:
            return "Error: increasing value is 'a' or 'g'"

    else:
        pass

    pers = Pers(mt)
    act = Actuarial(i, pers)
    if not incr and not deff and not wh_l and not post:
        return act.aaxn(x, n, m)
    elif not incr and not deff and not wh_l and post:
        return act.axn(x, n, m)
    elif not incr and not deff and wh_l and not post:
        return act.aax(x, m)
    elif not incr and not deff and wh_l and post:
        return act.ax(x, m)
    elif not incr and deff and not wh_l and not post:
        return act.taaxn(x, n, t, m)
    elif not incr and deff and not wh_l and post:
        return act.taxn(x, n, t, m)
    elif not incr and deff and wh_l and not post:
        return act.taax(x, t, m)
    elif not incr and deff and wh_l and post:
        return act.tax(x, t, m)
    elif incr and not deff and not wh_l and not post:
        return act.qaaxn(x, n, q, m)
    elif incr and not deff and not wh_l and post:
        return act.qAxn(x, n, q, m)
    elif incr and not deff and wh_l and not post:
        return act.qaax(x, q, m)
    elif incr and not deff and wh_l and post:
        return act.qAx(x, q, m)
    elif incr and deff and not wh_l and not post:
        return act.qtaaxn(x, n, t, q, m)
    elif incr and deff and not wh_l and post:
        return act.qtaxn(x, n, t, q, m)
    elif incr and deff and wh_l and not post:
        return act.qtaax(x, t, q, m)
    else:
        # elif incr and deff and wh_l and post:
        return act.Itax(x, t)
