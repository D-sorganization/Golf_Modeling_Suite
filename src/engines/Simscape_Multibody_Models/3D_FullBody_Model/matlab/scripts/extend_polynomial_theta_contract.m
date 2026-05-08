function report = extend_polynomial_theta_contract(varargin)
%EXTEND_POLYNOMIAL_THETA_CONTRACT Add full-body leg polynomial coefficients.
%   REPORT = EXTEND_POLYNOMIAL_THETA_CONTRACT() appends the left/right hip,
%   knee, and ankle coefficient families to the full-body
%   PolynomialInputValues.mat file using the same <Family><A..G> discovery
%   contract as getPolynomialParameterInfo().
%
%   The helper is intentionally idempotent. Existing coefficient variables are
%   preserved unless opts.overwrite is true.

    opts = local_parse_options(varargin{:});
    coefficient_letters = {'A', 'B', 'C', 'D', 'E', 'F', 'G'};
    leg_families = { ...
        'LHipX', 'LHipY', 'LHipZ', 'LKnee', 'LAnkleX', 'LAnkleY', ...
        'RHipX', 'RHipY', 'RHipZ', 'RKnee', 'RAnkleX', 'RAnkleY'};

    existing = load(opts.mat_path);
    before_names = fieldnames(existing);
    payload = existing;
    added_names = {};
    preserved_names = {};

    for family_idx = 1:numel(leg_families)
        family = leg_families{family_idx};
        for coeff_idx = 1:numel(coefficient_letters)
            name = [family coefficient_letters{coeff_idx}];
            if isfield(payload, name) && ~opts.overwrite
                preserved_names{end + 1} = name; %#ok<AGROW>
            else
                payload.(name) = 0.0;
                added_names{end + 1} = name; %#ok<AGROW>
            end
        end
    end

    save(opts.mat_path, '-struct', 'payload');

    info = local_discover_contract(opts.mat_path);
    report = struct();
    report.mat_path = opts.mat_path;
    report.before_variable_count = numel(before_names);
    report.after_variable_count = numel(fieldnames(payload));
    report.leg_families = leg_families;
    report.leg_family_count = numel(leg_families);
    report.added_names = added_names;
    report.preserved_names = preserved_names;
    report.discovered_joint_families = info.joint_names;
    report.discovered_joint_family_count = numel(info.joint_names);
    report.theta_size = info.total_params;
    report.expected_theta_size = 273;
    report.status = 'ok';

    if info.total_params ~= report.expected_theta_size
        report.status = 'unexpected_theta_size';
        error('FullBody:UnexpectedThetaSize', ...
            'Expected full-body theta size %d, discovered %d from %s.', ...
            report.expected_theta_size, info.total_params, opts.mat_path);
    end
end

function opts = local_parse_options(varargin)
    script_dir = fileparts(mfilename('fullpath'));
    default_mat_path = fullfile(script_dir, '..', 'src', 'model', ...
        'PolynomialInputValues.mat');

    opts = struct();
    opts.mat_path = default_mat_path;
    opts.overwrite = false;

    if nargin == 1 && isstruct(varargin{1})
        incoming = varargin{1};
        names = fieldnames(incoming);
        for i = 1:numel(names)
            opts.(names{i}) = incoming.(names{i});
        end
    elseif mod(nargin, 2) == 0
        for i = 1:2:nargin
            opts.(varargin{i}) = varargin{i + 1};
        end
    else
        error('FullBody:BadOptions', ...
            'Options must be a struct or name/value pairs.');
    end

    opts.mat_path = char(opts.mat_path);
end

function info = local_discover_contract(mat_path)
    loaded_data = load(mat_path);
    var_names = fieldnames(loaded_data);
    joint_map = containers.Map();

    for i = 1:numel(var_names)
        name = var_names{i};
        if strlength(name) > 1
            coeff = extractAfter(name, strlength(name) - 1);
            base_name = extractBefore(name, strlength(name));

            if isKey(joint_map, base_name)
                joint_map(base_name) = [joint_map(base_name), char(coeff)];
            else
                joint_map(base_name) = char(coeff);
            end
        end
    end

    all_joint_names = keys(joint_map);
    filtered_joint_names = {};

    for i = 1:numel(all_joint_names)
        joint_name = all_joint_names{i};
        coeffs = sort(joint_map(joint_name));

        if length(coeffs) == 7 && strcmp(coeffs, 'ABCDEFG')
            filtered_joint_names{end + 1} = joint_name; %#ok<AGROW>
        end
    end

    info = struct();
    info.joint_names = sort(filtered_joint_names);
    info.total_params = numel(info.joint_names) * 7;
end
