import scipy.io as sio
import numpy as np
from sklearn.cross_validation import train_test_split
from sklearn.utils import shuffle


# collect interictal, thresholded MI epochs from the interictal data structures
def getinterictal(fname):

    matfile = sio.loadmat(fname) # load mat file
    fv = matfile['data'][0, 0][0] # initialize first row
    for i in range(1, len(matfile['data'][0])): # collect remaining rows
        # print(np.shape(fv))
        # print(np.shape(matfile['data'][0, i][0]))

        fv = np.vstack((fv, matfile['data'][0, i][0])) # use vstack to vertically concatenate
    return fv


# collect thresholded MI epochs from a seizure
def getseizure(fname, max_windows):

    matfile = sio.loadmat(fname)  # load mat file
    fv = matfile['data'][0, 0][list(matfile['data'].dtype.names).index('fv')]  # initialize first row
    fl = matfile['data'][0, 0][list(matfile['data'].dtype.names).index('label')]
    prev_seiz = matfile['data'][0, 0][list(matfile['data'].dtype.names).index('Seizure')]
    cnt = 1
    keep = np.array([1])
    # print(prev_seiz)
    for i in range(1, len(matfile['data'][0])):  # collect remaining rows
        # print(np.shape(fv))
        # print(np.shape(matfile['data'][0, i][0]))
        curr_seiz = matfile['data'][0, i][list(matfile['data'].dtype.names).index('Seizure')]
        # print(curr_seiz)
        if curr_seiz == prev_seiz:
            cnt += 1
        else:
            prev_seiz = curr_seiz
            cnt = 1
        if cnt > max_windows:
            keep = np.vstack((keep, 0))
        else:
            keep = np.vstack((keep, 1))
        fv = np.vstack((fv, matfile['data'][0, i][list(matfile['data'].dtype.names).index('fv')]))  # use vstack to vertically concatenate
        fl = np.vstack((fl, matfile['data'][0, i][list(matfile['data'].dtype.names).index('label')]))
    return fv, fl, keep


# Compile the training and test set from the patient seizure and interictal data. Returns training and test data/labels;
#   The training data/labels are shuffled.
def gmi_dataset_extract(ldir, gmiType, winSize, threshold, stateSwitch, interTestSize, max_windows):  # random goes 2nd-to-last

    patients = ['DV', 'GB', 'SW', 'PE', 'RS', 'JY']
    if winSize == '10':
        test_rng = {'DV': [20, 27], 'GB': [4, 7], 'SW': [2, 3], 'PE': [2, 3], 'RS': [4, 5], 'JY': [8, 13]}
        train_rng = {'DV': [0, 19], 'GB': [0, 3], 'SW': [0, 1], 'PE': [0, 1], 'RS': [0, 3], 'JY': [0, 7]}
    elif winSize == '2':
        test_rng = {'DV': [100, 139], 'GB': [20, 39], 'SW': [10, 19], 'PE': [20, 29], 'RS': [20, 29], 'JY': [40, 69]}
        train_rng = {'DV': [0, 99], 'GB': [0, 19], 'SW': [0, 9], 'PE': [0, 19], 'RS': [0, 19], 'JY': [0, 39]}

    first = True  # first patient for initialization on first loop iter
    for pt in patients:
        fname = pt + "19_EEG_" + winSize + "sec_" + gmiType + "_th=%0.0d.mat" % threshold  # file of seizure data
        fv, fl, keep_inds = getseizure(ldir + fname, max_windows)  # feature values, feature labels, indices to keep
        if first:  # initialize the feature value, label, and keep ind stacks
            test_data = fv[test_rng[pt][0]:test_rng[pt][1] + 1]  # "+ 1" includes the last sample
            train_data = fv[train_rng[pt][0]:train_rng[pt][1] + 1]
            test_lbls = fl[test_rng[pt][0]:test_rng[pt][1] + 1]
            train_lbls = fl[train_rng[pt][0]:train_rng[pt][1] + 1]
            train_keep_inds = keep_inds[train_rng[pt][0]:train_rng[pt][1] + 1]
            test_keep_inds = keep_inds[test_rng[pt][0]:test_rng[pt][1] + 1]
            first = False  # switch the first patient flag
        else:  # start stacking
            test_data = np.vstack((test_data, fv[test_rng[pt][0]:test_rng[pt][1] + 1]))
            train_data = np.vstack((train_data, fv[train_rng[pt][0]:train_rng[pt][1] + 1]))
            test_lbls = np.vstack((test_lbls, fl[test_rng[pt][0]:test_rng[pt][1] + 1]))
            train_lbls = np.vstack((train_lbls, fl[train_rng[pt][0]:train_rng[pt][1] + 1]))
            train_keep_inds = np.vstack((train_keep_inds, keep_inds[train_rng[pt][0]:train_rng[pt][1] + 1]))
            test_keep_inds = np.vstack((test_keep_inds, keep_inds[test_rng[pt][0]:test_rng[pt][1] + 1]))

    # old debugging
    # print((test_keep_inds.ravel(), test_lbls.ravel()))
    #
    # print(np.where(np.logical_and(test_keep_inds.ravel(), test_lbls.ravel()) == True))
    #
    # # handle the keep indices
    # test_data = np.squeeze(test_data[np.where(test_keep_inds.ravel() == 0), ])
    # train_data = np.squeeze(train_data[np.where(train_keep_inds.ravel() == 0), ])
    # test_lbls = np.squeeze(test_lbls[np.where(test_keep_inds.ravel() == 0)])
    # train_lbls = np.squeeze(train_lbls[np.where(train_keep_inds.ravel() == 0)])

    # handle the state_switch
    if stateSwitch == "s1":
        test_data = np.squeeze(test_data[np.where(test_lbls.ravel() == 0), ])
        train_data = np.squeeze(train_data[np.where(train_lbls.ravel() == 0), ])
        test_lbls = np.ones([np.shape(test_data)[0], 1])
        train_lbls = np.ones([np.shape(train_data)[0], 1])
    elif stateSwitch == "s2":
        test_data = np.squeeze(test_data[np.where(np.logical_and(test_keep_inds.ravel(), test_lbls.ravel()) == True), ])
        train_data = np.squeeze(train_data[np.where(np.logical_and(train_keep_inds.ravel(), train_lbls.ravel()) == True), ])
        test_lbls = np.ones([np.shape(test_data)[0], 1])
        train_lbls = np.ones([np.shape(train_data)[0], 1])

    # old debugging
    # print(len(train_lbls))
    # print(len(test_lbls))
    # input("Press a key...")

    # get the interictal data (if s1 vs. i0 OR s2 vs. i0)
    if stateSwitch != "s1s2":
        fname = "6P19_EEG_" + winSize + "sec_" + gmiType + "_th=%0.0d.mat" % threshold
        fv = getinterictal(ldir + fname)
        fl = np.zeros([np.shape(fv)[0], 1])
        fv_train, fv_test, fl_train, fl_test = train_test_split(fv, fl, test_size=interTestSize)  #, random_state=randomState)

        # compile the final train and test set from both interictal and seizure states
        X_train = np.vstack((train_data, fv_train))
        X_test = np.vstack((test_data, fv_test))
        y_train = np.vstack((train_lbls, fl_train))
        y_test = np.vstack((test_lbls, fl_test))
        # print(np.shape(y_train) + np.shape(X_train))
        X_train, y_train = shuffle(X_train, y_train.ravel())  #, random_state=randomState)
    else:
        X_train = train_data
        X_test = test_data
        y_train = train_lbls
        y_test = test_lbls
        X_train, y_train = shuffle(X_train, y_train.ravel())  # , random_state=randomState)

    X_train = np.float_(X_train)
    X_test = np.float_(X_test)

    return X_train, y_train, X_test, y_test


def full_seizure_extract(fname):

    matfile = sio.loadmat(fname)
    fv = matfile['data'][0, 0][list(matfile['data'].dtype.names).index('fv')][0, 0]  # initialize first row
    wind = matfile['data'][0, 0][list(matfile['data'].dtype.names).index('wind')]
    for i in range(1, np.shape(matfile['data'][0, 0][list(matfile['data'].dtype.names).index('fv')])[1]):  # collect remaining rows
        # print(np.shape(fv))
        # print(np.shape(matfile['data'][0, i][0]))
        fv = np.vstack((fv, matfile['data'][0, 0][list(matfile['data'].dtype.names).index('fv')][0, i]))  # use vstack to vertically concatenate

    return fv, wind


def full_seizure_detect_save(fname, fv, classes, wind):
    print(fname)
    subdict = {'fv': fv, 'wind': wind, 'classes': classes}
    sio.savemat(fname, {'data': subdict})

    return None
