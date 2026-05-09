classdef test_3d_fullbody_polynomial_contract < matlab.unittest.TestCase
    % Tests for the full-body leg polynomial theta contract.

    methods(Test)
        function fullbodyPolynomialContractDiscoversThirtyNineFamilies(testCase)
            repo_root = test_3d_fullbody_polynomial_contract.local_repo_root();
            mat_path = fullfile(repo_root, 'src', 'engines', ...
                'Simscape_Multibody_Models', '3D_FullBody_Model', ...
                'matlab', 'src', 'model', 'PolynomialInputValues.mat');

            script_dir = fullfile(repo_root, 'src', 'engines', ...
                'Simscape_Multibody_Models', '3D_FullBody_Model', ...
                'matlab', 'scripts');
            addpath(script_dir);

            report = extend_polynomial_theta_contract('mat_path', mat_path);

            testCase.verifyEqual(report.discovered_joint_family_count, 39);
            testCase.verifyEqual(report.theta_size, 273);
            testCase.verifyEqual(report.leg_family_count, 12);
            testCase.verifyTrue(any(strcmp(report.discovered_joint_families, 'LHipX')));
            testCase.verifyTrue(any(strcmp(report.discovered_joint_families, 'RKnee')));
            testCase.verifyTrue(any(strcmp(report.discovered_joint_families, 'RAnkleY')));
        end

        function legacyPolynomialContractRemainsTwentySevenFamilies(testCase)
            repo_root = test_3d_fullbody_polynomial_contract.local_repo_root();
            mat_path = fullfile(repo_root, 'src', 'engines', ...
                'Simscape_Multibody_Models', '3D_Golf_Model', ...
                'matlab', 'src', 'model', 'PolynomialInputValues.mat');

            helper_dir = fullfile(repo_root, 'src', 'engines', ...
                'Simscape_Multibody_Models', '3D_Golf_Model', ...
                'matlab', 'src', 'functions', 'dataset_generator');
            addpath(helper_dir);

            info = getPolynomialParameterInfo(mat_path);

            testCase.verifyEqual(numel(info.joint_names), 27);
            testCase.verifyEqual(info.total_params, 189);
            testCase.verifyEqual(info.coefficients_per_joint, 7);
        end
    end

    methods(Static, Access=private)
        function repo_root = local_repo_root()
            here = fileparts(mfilename('fullpath'));
            repo_root = fullfile(here, '..', '..', '..', '..', '..', '..');
            repo_root = char(java.io.File(repo_root).getCanonicalPath());
        end
    end
end
