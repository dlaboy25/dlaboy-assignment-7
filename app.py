from flask import Flask, render_template, request, url_for, session
from flask_session import Session  # Import Flask-Session
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy import stats
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with your own secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
# Optionally specify a directory for session files
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
Session(app)  # Initialize the extension

# Ensure the session directory exists
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    os.makedirs(app.config['SESSION_FILE_DIR'])


def generate_data(N, mu, beta0, beta1, sigma2, S):
    # Generate data and initial plots

    # Generate a random dataset X of size N with values between 0 and 1
    X = np.random.uniform(0, 1, N)

    # Generate a random dataset Y using the specified beta0, beta1, mu, and sigma2
    # Y = beta0 + beta1 * X + mu + error term
    error = np.random.normal(0, np.sqrt(sigma2), N)
    Y = beta0 + beta1 * X + mu + error

    # Fit a linear regression model to X and Y
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), Y)
    slope = model.coef_[0]
    intercept = model.intercept_

    # Generate a scatter plot of (X, Y) with the fitted regression line
    plot1_path = "static/plot1.png"
    plt.figure()
    plt.scatter(X, Y, color='blue', label='Data')
    plt.plot(X, model.predict(X.reshape(-1, 1)), color='red', label='Regression Line')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Scatter Plot with Regression Line')
    plt.legend()
    plt.savefig(plot1_path)
    plt.close()

    # Run S simulations to generate slopes and intercepts
    slopes = []
    intercepts = []

    for _ in range(S):
        # Generate simulated datasets using the same beta0 and beta1
        X_sim = np.random.uniform(0, 1, N)
        error_sim = np.random.normal(0, np.sqrt(sigma2), N)
        Y_sim = beta0 + beta1 * X_sim + mu + error_sim

        # Fit linear regression to simulated data and store slope and intercept
        sim_model = LinearRegression()
        sim_model.fit(X_sim.reshape(-1, 1), Y_sim)
        sim_slope = sim_model.coef_[0]
        sim_intercept = sim_model.intercept_

        slopes.append(sim_slope)
        intercepts.append(sim_intercept)

    # Plot histograms of slopes and intercepts
    plot2_path = "static/plot2.png"
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.hist(slopes, bins=20, color='skyblue', edgecolor='black')
    plt.title('Histogram of Slopes')
    plt.xlabel('Slope')
    plt.ylabel('Frequency')

    plt.subplot(1, 2, 2)
    plt.hist(intercepts, bins=20, color='salmon', edgecolor='black')
    plt.title('Histogram of Intercepts')
    plt.xlabel('Intercept')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig(plot2_path)
    plt.close()

    # Return data needed for further analysis
    slope_more_extreme = None
    intercept_extreme = None

    return (
        X,
        Y,
        slope,
        intercept,
        plot1_path,
        plot2_path,
        slope_more_extreme,
        intercept_extreme,
        slopes,
        intercepts,
    )


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    # Get user input from the form
    N = int(request.form["N"])
    mu = float(request.form["mu"])
    sigma2 = float(request.form["sigma2"])
    beta0 = float(request.form["beta0"])
    beta1 = float(request.form["beta1"])
    S = int(request.form["S"])

    # Generate data and initial plots
    (
        X,
        Y,
        slope,
        intercept,
        plot1,
        plot2,
        slope_extreme,
        intercept_extreme,
        slopes,
        intercepts,
    ) = generate_data(N, mu, beta0, beta1, sigma2, S)

    # Store data in session
    session["X"] = X.tolist()
    session["Y"] = Y.tolist()
    session["slope"] = slope
    session["intercept"] = intercept
    session["slopes"] = slopes
    session["intercepts"] = intercepts
    session["slope_extreme"] = slope_extreme
    session["intercept_extreme"] = intercept_extreme
    session["N"] = N
    session["mu"] = mu
    session["sigma2"] = sigma2
    session["beta0"] = beta0
    session["beta1"] = beta1
    session["S"] = S

    # Return render_template with variables
    return render_template(
        "index.html",
        plot1=plot1,
        plot2=plot2,
        slope_extreme=slope_extreme,
        intercept_extreme=intercept_extreme,
        N=N,
        mu=mu,
        sigma2=sigma2,
        beta0=beta0,
        beta1=beta1,
        S=S,
    )


@app.route("/hypothesis_test", methods=["POST"])
def hypothesis_test():
    # Retrieve data from session
    N = session.get("N")
    S = session.get("S")
    slope = session.get("slope")
    intercept = session.get("intercept")
    slopes = session.get("slopes")
    intercepts = session.get("intercepts")
    beta0 = session.get("beta0")
    beta1 = session.get("beta1")

    # Check if session data exists
    if None in (N, S, slope, intercept, slopes, intercepts, beta0, beta1):
        return render_template("index.html", error="Session data is missing. Please generate data first.")

    N = int(N)
    S = int(S)
    slope = float(slope)
    intercept = float(intercept)
    slopes = slopes
    intercepts = intercepts
    beta0 = float(beta0)
    beta1 = float(beta1)

    parameter = request.form.get("parameter")
    test_type = request.form.get("test_type")

    # Use the slopes or intercepts from the simulations
    if parameter == "slope":
        simulated_stats = np.array(slopes)
        observed_stat = slope
        hypothesized_value = beta1
    else:
        simulated_stats = np.array(intercepts)
        observed_stat = intercept
        hypothesized_value = beta0

    # Calculate p-value based on test type
    if test_type == '>':
        p_value = np.mean(simulated_stats >= observed_stat)
    elif test_type == '<':
        p_value = np.mean(simulated_stats <= observed_stat)
    elif test_type == '!=':
        p_value = np.mean(np.abs(simulated_stats - hypothesized_value) >= np.abs(observed_stat - hypothesized_value))
    else:
        p_value = None

    # If p_value is very small, set fun_message
    if p_value is not None and p_value <= 0.0001:
        fun_message = "Wow! You have encountered a rare event!"
    else:
        fun_message = None

    # Plot histogram of simulated statistics
    plot3_path = "static/plot3.png"
    plt.figure()
    plt.hist(simulated_stats, bins=20, color='lightgreen', edgecolor='black')
    plt.axvline(x=observed_stat, color='red', linestyle='--', label='Observed Statistic')
    plt.axvline(x=hypothesized_value, color='blue', linestyle='-', label='Hypothesized Value')
    plt.xlabel(parameter.capitalize())
    plt.ylabel('Frequency')
    plt.title('Histogram of Simulated ' + parameter.capitalize())
    plt.legend()
    plt.savefig(plot3_path)
    plt.close()

    # Return results to template
    return render_template(
        "index.html",
        plot1="static/plot1.png",
        plot2="static/plot2.png",
        plot3=plot3_path,
        parameter=parameter,
        observed_stat=observed_stat,
        hypothesized_value=hypothesized_value,
        N=N,
        beta0=beta0,
        beta1=beta1,
        S=S,
        p_value=p_value,
        fun_message=fun_message,
    )


@app.route("/confidence_interval", methods=["POST"])
def confidence_interval():
    # Retrieve data from session
    N = session.get("N")
    mu = session.get("mu")
    sigma2 = session.get("sigma2")
    beta0 = session.get("beta0")
    beta1 = session.get("beta1")
    S = session.get("S")
    X = session.get("X")
    Y = session.get("Y")
    slope = session.get("slope")
    intercept = session.get("intercept")
    slopes = session.get("slopes")
    intercepts = session.get("intercepts")

    # Check if session data exists
    if None in (N, mu, sigma2, beta0, beta1, S, X, Y, slope, intercept, slopes, intercepts):
        return render_template("index.html", error="Session data is missing. Please generate data first.")

    N = int(N)
    mu = float(mu)
    sigma2 = float(sigma2)
    beta0 = float(beta0)
    beta1 = float(beta1)
    S = int(S)
    X = np.array(X)
    Y = np.array(Y)
    slope = float(slope)
    intercept = float(intercept)
    slopes = slopes
    intercepts = intercepts

    parameter = request.form.get("parameter")
    confidence_level = float(request.form.get("confidence_level"))

    # Use the slopes or intercepts from the simulations
    if parameter == "slope":
        estimates = np.array(slopes)
        observed_stat = slope
        true_param = beta1
    else:
        estimates = np.array(intercepts)
        observed_stat = intercept
        true_param = beta0

    # Calculate mean and standard deviation of the estimates
    mean_estimate = np.mean(estimates)
    std_estimate = np.std(estimates, ddof=1)

    # Calculate confidence interval for the parameter estimate
    alpha = 1 - (confidence_level / 100)
    ci_lower = np.percentile(estimates, (alpha / 2) * 100)
    ci_upper = np.percentile(estimates, (1 - alpha / 2) * 100)

    # Check if confidence interval includes true parameter
    includes_true = 'Yes' if ci_lower <= true_param <= ci_upper else 'No'

    # Plot the individual estimates as gray points and confidence interval
    plot4_path = "static/plot4.png"
    plt.figure()
    x_jitter = np.random.uniform(-0.1, 0.1, size=estimates.size)
    plt.scatter(x_jitter, estimates, color='gray', alpha=0.5, label='Simulated Estimates')

    # Plot mean estimate
    mean_color = 'green' if includes_true == 'Yes' else 'red'
    plt.scatter(0, mean_estimate, color=mean_color, s=100, label='Mean Estimate')

    # Plot confidence interval
    plt.hlines(y=[ci_lower, ci_upper], xmin=-0.2, xmax=0.2, colors='blue', label='Confidence Interval')

    # Plot true parameter value
    plt.scatter(0, true_param, color='black', marker='x', s=100, label='True Parameter')

    plt.xlim(-0.5, 0.5)
    plt.xlabel('Simulations')
    plt.ylabel(parameter.capitalize())
    plt.title(f'{confidence_level}% Confidence Interval for {parameter.capitalize()}')
    plt.legend()
    plt.savefig(plot4_path)
    plt.close()

    # Return results to template
    return render_template(
        "index.html",
        plot1="static/plot1.png",
        plot2="static/plot2.png",
        plot4=plot4_path,
        parameter=parameter,
        confidence_level=confidence_level,
        mean_estimate=mean_estimate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        includes_true=includes_true,
        observed_stat=observed_stat,
        N=N,
        mu=mu,
        sigma2=sigma2,
        beta0=beta0,
        beta1=beta1,
        S=S,
    )


if __name__ == "__main__":
    app.run(debug=True)
