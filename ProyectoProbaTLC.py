# toolkit

import math
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def normal_pdf(x, mu, var):
    if var <= 0:
        return np.zeros_like(x)
    s = math.sqrt(var)
    return (1.0 / (s * math.sqrt(2.0 * math.pi))) * np.exp(-0.5 * ((x - mu) / s) ** 2)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Toolkit TLC (Opcion 2) - GUI")

        # ---------- Layout principal ----------
        root.columnconfigure(0, weight=0)  # panel izquierdo
        root.columnconfigure(1, weight=1)  # grafica / salida
        root.rowconfigure(0, weight=1)

        self.left = ttk.Frame(root, padding=10)
        self.left.grid(row=0, column=0, sticky="ns")

        self.right = ttk.Frame(root, padding=10)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=1)
        self.right.rowconfigure(1, weight=1)

        # ---------- controles ----------
        ttk.Label(self.left, text="Distribucion base:").grid(row=0, column=0, sticky="w")

        self.dist_var = tk.StringVar(value="Uniforme(a,b)")
        self.dist_combo = ttk.Combobox(
            self.left,
            textvariable=self.dist_var,
            state="readonly",
            values=["Uniforme(a,b)", "Exponencial(lambda)", "Bernoulli(p)", "Binomial(m,p)"]
        )
        self.dist_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.dist_combo.bind("<<ComboboxSelected>>", self.on_dist_change)

        # Parametros dinamicos
        self.params_frame = ttk.LabelFrame(self.left, text="Parametros", padding=10)
        self.params_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.param_entries = {}  # nombre -> Entry
        self.build_param_inputs("Uniforme(a,b)")

        # n y N
        self.nn_frame = ttk.LabelFrame(self.left, text="Muestreo", padding=10)
        self.nn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(self.nn_frame, text="n (tamano muestral):").grid(row=0, column=0, sticky="w")
        self.n_entry = ttk.Entry(self.nn_frame)
        self.n_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.n_entry.insert(0, "30")

        ttk.Label(self.nn_frame, text="N (repeticiones):").grid(row=2, column=0, sticky="w")
        self.N_entry = ttk.Entry(self.nn_frame)
        self.N_entry.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.N_entry.insert(0, "1000")

        # Semilla (opcional)
        self.seed_var = tk.IntVar(value=0)
        self.seed_check = ttk.Checkbutton(self.nn_frame, text="Fijar semilla", variable=self.seed_var, command=self.toggle_seed)
        self.seed_check.grid(row=4, column=0, sticky="w")

        self.seed_entry = ttk.Entry(self.nn_frame, state="disabled")
        self.seed_entry.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.seed_entry.insert(0, "123")

        # IC
        self.ic_var = tk.IntVar(value=0)
        self.ic_check = ttk.Checkbutton(self.nn_frame, text="Cobertura de IC (opcional)", variable=self.ic_var, command=self.toggle_ic)
        self.ic_check.grid(row=6, column=0, sticky="w")

        self.conf_entry = ttk.Entry(self.nn_frame, state="disabled")
        self.conf_entry.grid(row=7, column=0, sticky="ew", pady=(0, 8))
        self.conf_entry.insert(0, "0.95")

    
        self.btn_frame = ttk.Frame(self.left)
        self.btn_frame.grid(row=4, column=0, sticky="ew")

        self.run_btn = ttk.Button(self.btn_frame, text="Simular", command=self.run_sim)
        self.run_btn.grid(row=0, column=0, sticky="ew")

        self.clear_btn = ttk.Button(self.btn_frame, text="Limpiar", command=self.clear_output)
        self.clear_btn.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    
        # Grafica embebida
        self.fig = Figure(figsize=(6.5, 4.0), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Histograma de Xbar + Normal teorica")
        self.ax.set_xlabel("Xbar")
        self.ax.set_ylabel("Densidad")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Resumen (texto)
        self.summary = tk.Text(self.right, height=12)
        self.summary.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.summary.insert("1.0", "Aqui aparecera el resumen numerico...\n")

        # Estiramiento
        for w in [self.left, self.params_frame, self.nn_frame]:
            w.columnconfigure(0, weight=1)

    # ---------- UI helpers ----------
    def toggle_seed(self):
        if self.seed_var.get() == 1:
            self.seed_entry.config(state="normal")
        else:
            self.seed_entry.config(state="disabled")

    def toggle_ic(self):
        if self.ic_var.get() == 1:
            self.conf_entry.config(state="normal")
        else:
            self.conf_entry.config(state="disabled")

    def on_dist_change(self, event=None):
        self.build_param_inputs(self.dist_var.get())

    def build_param_inputs(self, dist_name):
        
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.param_entries.clear()

        # campos segun distribucion
        if dist_name == "Uniforme(a,b)":
            self.add_param("a", "0")
            self.add_param("b", "1")
        elif dist_name == "Exponencial(lambda)":
            self.add_param("lambda", "1")
        elif dist_name == "Bernoulli(p)":
            self.add_param("p", "0.5")
        elif dist_name == "Binomial(m,p)":
            self.add_param("m", "10")
            self.add_param("p", "0.5")

    def add_param(self, name, default):
        row = len(self.param_entries) * 2
        ttk.Label(self.params_frame, text=f"{name}:").grid(row=row, column=0, sticky="w")
        e = ttk.Entry(self.params_frame)
        e.grid(row=row + 1, column=0, sticky="ew", pady=(0, 8))
        e.insert(0, default)
        self.param_entries[name] = e

    def clear_output(self):
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "Aqui aparecera el resumen numerico...\n")
        self.ax.clear()
        self.ax.set_title("Histograma de Xbar + Normal teorica")
        self.ax.set_xlabel("Xbar")
        self.ax.set_ylabel("Densidad")
        self.ax.grid(True)
        self.canvas.draw()

    # ---------- Validacion ----------
    def get_int(self, entry, field_name, minimo=None):
        try:
            x = int(entry.get().strip())
        except ValueError:
            raise ValueError(f"{field_name} debe ser entero.")
        if minimo is not None and x < minimo:
            raise ValueError(f"{field_name} debe ser >= {minimo}.")
        return x

    def get_float(self, entry, field_name, minimo=None, maximo=None):
        try:
            x = float(entry.get().strip())
        except ValueError:
            raise ValueError(f"{field_name} debe ser numero.")
        if minimo is not None and x < minimo:
            raise ValueError(f"{field_name} debe ser >= {minimo}.")
        if maximo is not None and x > maximo:
            raise ValueError(f"{field_name} debe ser <= {maximo}.")
        return x

    # ---------- Core: mu, var, sampler ----------
    def build_model(self):
        dist = self.dist_var.get()

        if dist == "Uniforme(a,b)":
            a = self.get_float(self.param_entries["a"], "a")
            b = self.get_float(self.param_entries["b"], "b")
            if b <= a:
                raise ValueError("En Uniforme, b debe ser mayor que a.")
            mu = (a + b) / 2.0
            var = ((b - a) ** 2) / 12.0

            def sampler(N, n):
                return np.random.uniform(a, b, size=(N, n))

            nombre = f"Uniforme(a={a}, b={b})"
            return nombre, mu, var, sampler

        if dist == "Exponencial(lambda)":
            lam = self.get_float(self.param_entries["lambda"], "lambda", minimo=1e-12)
            mu = 1.0 / lam
            var = 1.0 / (lam ** 2)

            def sampler(N, n):
                return np.random.exponential(scale=1.0 / lam, size=(N, n))

            nombre = f"Exponencial(lambda={lam})"
            return nombre, mu, var, sampler

        if dist == "Bernoulli(p)":
            p = self.get_float(self.param_entries["p"], "p", minimo=0.0, maximo=1.0)
            if not (0.0 < p < 1.0):
                raise ValueError("En Bernoulli, p debe estar entre 0 y 1 (sin incluir).")
            mu = p
            var = p * (1.0 - p)

            def sampler(N, n):
                return np.random.binomial(1, p, size=(N, n))

            nombre = f"Bernoulli(p={p})"
            return nombre, mu, var, sampler

        # Binomial(m,p)
        m = self.get_int(self.param_entries["m"], "m", minimo=1)
        p = self.get_float(self.param_entries["p"], "p", minimo=0.0, maximo=1.0)
        if not (0.0 < p < 1.0):
            raise ValueError("En Binomial, p debe estar entre 0 y 1 (sin incluir).")

        mu = m * p
        var = m * p * (1.0 - p)

        def sampler(N, n):
            return np.random.binomial(m, p, size=(N, n))

        nombre = f"Binomial(m={m}, p={p})"
        return nombre, mu, var, sampler

    def run_sim(self):
        try:
            # Seed (opcional)
            if self.seed_var.get() == 1:
                seed = self.get_int(self.seed_entry, "Semilla", minimo=0)
                np.random.seed(seed)

            n = self.get_int(self.n_entry, "n", minimo=1)
            N = self.get_int(self.N_entry, "N", minimo=1)

            nombre, mu, var, sampler = self.build_model()

            # Simular
            datos = sampler(N, n)
            xbar = datos.mean(axis=1)

            # Empirico
            mu_emp = float(np.mean(xbar))
            var_emp = float(np.var(xbar, ddof=1)) if N > 1 else float(np.var(xbar))

            # TLC
            var_teo = var / n
            se_teo = math.sqrt(var_teo)

            # Opcional: cobertura IC 
            cobertura = None
            conf = None
            if self.ic_var.get() == 1:
                conf = self.get_float(self.conf_entry, "Confianza", minimo=0.5, maximo=0.999999)
                from statistics import NormalDist
                alpha = 1.0 - conf
                z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
                li = xbar - z * se_teo
                ls = xbar + z * se_teo
                cobertura = float(np.mean((li <= mu) & (mu <= ls)))


            self.summary.delete("1.0", "end")
            out = []
            out.append("=== Resumen ===\n")
            out.append(f"Distribucion base: {nombre}\n")
            out.append(f"n (tamano muestral): {n}\n")
            out.append(f"N (repeticiones): {N}\n\n")

            out.append("--- Teorico ---\n")
            out.append(f"mu = E[X]: {mu}\n")
            out.append(f"var(X): {var}\n")
            out.append(f"var(Xbar) = var(X)/n: {var_teo}\n")
            out.append(f"SE = sqrt(var(Xbar)): {se_teo}\n\n")

            out.append("--- Empirico (simulacion) ---\n")
            out.append(f"media(Xbar): {mu_emp}\n")
            out.append(f"var(Xbar): {var_emp}\n")
            out.append(f"error |media_emp - mu|: {abs(mu_emp - mu)}\n")
            out.append(f"error |var_emp - var_teo|: {abs(var_emp - var_teo)}\n")

            if cobertura is not None:
                out.append("\n--- IC (aprox normal) ---\n")
                out.append(f"Nivel de confianza: {conf}\n")
                out.append(f"Cobertura empirica: {cobertura}\n")

            self.summary.insert("1.0", "".join(out))

            # histograma + normal teorica
            self.ax.clear()
            self.ax.grid(True)
            self.ax.set_title("Histograma de Xbar + Normal teorica")
            self.ax.set_xlabel("Xbar")
            self.ax.set_ylabel("Densidad")

            bins = max(10, int(math.sqrt(N)))
            self.ax.hist(xbar, bins=bins, density=True)

            xmin = float(np.min(xbar))
            xmax = float(np.max(xbar))
            pad = 3.0 * se_teo if se_teo > 0 else 1.0
            xs = np.linspace(xmin - pad, xmax + pad, 400)
            ys = normal_pdf(xs, mu, var_teo)
            self.ax.plot(xs, ys, linewidth=2)

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass

    app = App(root)
    root.minsize(950, 600)
    root.mainloop()


if __name__ == "__main__":
    main()
