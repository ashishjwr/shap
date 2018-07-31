import numpy as np


def remove(nmask, X_train, y_train, X_test, y_test, attr_test, model_generator, metric):
    """ The model is retrained for each test sample with the important features set to a constant.

    If you want to know how important a set of features is you can ask how the model would be
    different if those features had never existed. To determine this we can mask those features
    across the entire training and test datasets, then retrain the model. If we apply compare the
    output of this retrained model to the original model we can see the effect produced by knowning
    the features we masked. Since for individualized explanation methods each test sample has a
    different set of most important features we need to retrain the model for every test sample
    to get the change in model performance when a specified fraction of the most important features
    are withheld.
    """

    X_train, X_test = to_array(X_train, X_test)

    # how many features to mask
    assert X_train.shape[1] == X_test.shape[1]

    # train a model without masking
    model = model_generator()
    model.fit(X_train, y_train)

    # mask nmask top features and re-train the model for each test explanation
    X_train_tmp = np.zeros(X_train.shape)
    X_test_tmp = np.zeros(X_test.shape)
    yp_masked_test = np.zeros(y_test.shape)
    tie_breaking_noise = const_rand(X_train.shape[1]) * 1e-6
    for i in range(len(y_test)):
        if nmask[i] == 0:
            yp_masked_test[i] = model.predict(X_test[i:i+1])[0]
        else:
            # mask out the most important features for this test instance
            X_train_tmp[:] = X_train
            X_test_tmp[:] = X_test
            ordering = np.argsort(-attr_test[i,:] + tie_breaking_noise)
            X_train_tmp[:,ordering[:nmask[i]]] = X_train[:,ordering[:nmask[i]]].mean()
            X_test_tmp[:,ordering[:nmask[i]]] = X_train[:,ordering[:nmask[i]]].mean()

            # retrain the model and make a prediction
            model_masked = model_generator()
            model_masked.fit(X_train_tmp, y_train)
            yp_masked_test[i] = model_masked.predict(X_test_tmp[i:i+1])[0]

    return metric(y_test, yp_masked_test)

def batch_remove(nmask_train, nmask_test, X_train, y_train, X_test, y_test, attr_train, attr_test, model_generator, metric):
    """ An approximation of holdout that only retraines the model once.

    This is alse called ROAR (RemOve And Retrain) in work by Google. It is much more computationally
    efficient that the holdout method because it masks the most important features in every sample
    and then retrains the model once, instead of retraining the model for every test sample like
    the holdout metric.
    """

    X_train, X_test = to_array(X_train, X_test)

    # how many features to mask
    assert X_train.shape[1] == X_test.shape[1]

    # mask nmask top features for each explanation
    X_train_tmp = X_train.copy()
    X_train_mean = X_train.mean(0)
    tie_breaking_noise = const_rand(X_train.shape[1]) * 1e-6
    for i in range(len(y_train)):
        if nmask_train[i] > 0:
            ordering = np.argsort(-attr_train[i, :] + tie_breaking_noise)
            X_train_tmp[i, ordering[:nmask_train[i]]] = X_train_mean[ordering[:nmask_train[i]]]
    X_test_tmp = X_test.copy()
    for i in range(len(y_test)):
        if nmask_test[i] > 0:
            ordering = np.argsort(-attr_test[i, :] + tie_breaking_noise)
            X_test_tmp[i, ordering[:nmask_test[i]]] = X_train_mean[ordering[:nmask_test[i]]]

    # train the model with all the given features masked
    model_masked = model_generator()
    model_masked.fit(X_train_tmp, y_train)
    yp_test_masked = model_masked.predict(X_test_tmp)

    return metric(y_test, yp_test_masked)

def keep(nkeep, X_train, y_train, X_test, y_test, attr_test, model_generator, metric):
    """ The model is retrained for each test sample with the non-important features set to a constant.

    If you want to know how important a set of features is you can ask how the model would be
    different if only those features had existed. To determine this we can mask the other features
    across the entire training and test datasets, then retrain the model. If we apply compare the
    output of this retrained model to the original model we can see the effect produced by only
    knowning the important features. Since for individualized explanation methods each test sample
    has a different set of most important features we need to retrain the model for every test sample
    to get the change in model performance when a specified fraction of the most important features
    are retained.
    """

    X_train, X_test = to_array(X_train, X_test)

    # how many features to mask
    assert X_train.shape[1] == X_test.shape[1]

    # keep nkeep top features and re-train the model for each test explanation
    X_train_tmp = np.zeros(X_train.shape)
    X_test_tmp = np.zeros(X_test.shape)
    yp_masked_test = np.zeros(y_test.shape)
    tie_breaking_noise = const_rand(X_train.shape[1]) * 1e-6
    for i in range(len(y_test)):
        # mask out the most important features for this test instance
        X_train_tmp[:] = X_train
        X_test_tmp[:] = X_test
        ordering = np.argsort(-attr_test[i,:] + tie_breaking_noise)
        X_train_tmp[:,ordering[nkeep[i]:]] = X_train[:,ordering[nkeep[i]:]].mean()
        X_test_tmp[:,ordering[nkeep[i]:]] = X_train[:,ordering[nkeep[i]:]].mean()

        # retrain the model and make a prediction
        model_masked = model_generator()
        model_masked.fit(X_train_tmp, y_train)
        yp_masked_test[i] = model_masked.predict(X_test_tmp[i:i+1])[0]

    return metric(y_test, yp_masked_test)

def batch_keep(nkeep_train, nkeep_test, X_train, y_train, X_test, y_test, attr_train, attr_test, model_generator, metric):
    """ An approximation of keep that only retraines the model once.

    This is alse called KAR (Keep And Retrain) in work by Google. It is much more computationally
    efficient that the keep method because it masks the unimportant features in every sample
    and then retrains the model once, instead of retraining the model for every test sample like
    the keep metric.
    """

    X_train, X_test = to_array(X_train, X_test)

    # how many features to mask
    assert X_train.shape[1] == X_test.shape[1]

    # mask nkeep top features for each explanation
    X_train_tmp = X_train.copy()
    X_train_mean = X_train.mean(0)
    tie_breaking_noise = const_rand(X_train.shape[1]) * 1e-6
    for i in range(len(y_train)):
        if nkeep_train[i] < X_train.shape[1]:
            ordering = np.argsort(-attr_train[i, :] + tie_breaking_noise)
            X_train_tmp[i, ordering[nkeep_train[i]:]] = X_train_mean[ordering[nkeep_train[i]:]]
    X_test_tmp = X_test.copy()
    for i in range(len(y_test)):
        if nkeep_test[i] < X_test.shape[1]:
            ordering = np.argsort(-attr_test[i, :] + tie_breaking_noise)
            X_test_tmp[i, ordering[nkeep_test[i]:]] = X_train_mean[ordering[nkeep_test[i]:]]

    # train the model with all the features not given masked
    model_masked = model_generator()
    model_masked.fit(X_train_tmp, y_train)
    yp_test_masked = model_masked.predict(X_test_tmp)

    return metric(y_test, yp_test_masked)

def to_array(*args):
    return [a.values if str(type(a)).endswith("'pandas.core.frame.DataFrame'>") else a for a in args]

def const_rand(size, seed=23980):
    """ Generate a random array with a fixed seed.
    """
    old_seed = np.random.seed()
    np.random.seed(seed)
    out = np.random.rand(size)
    np.random.seed(old_seed)
    return out
